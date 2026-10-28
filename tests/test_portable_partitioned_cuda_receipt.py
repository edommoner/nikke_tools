"""The fast path retains source/receipt/image checks and never falls back."""
import contextlib,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_partitioned_cuda_receipt as pinned
import portable_partitioned_cuda_origin as origin
import portable_linked_artifact as linked
import portable_backend as backend
s=importlib.util.spec_from_file_location('pinned_receipt_cli',ROOT/'scripts/nikke_gpu.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


class ReceiptTests(unittest.TestCase):
    def fixture(self,root):
        auditor=root/'auditor';capture=root/'capture';old=root/'old'
        for p in (auditor,capture,old/'proof'):p.mkdir(parents=True)
        manifest=dict(suite='frozen',golden=dict(entries=[dict(name='one')],source_sha256={'gpu':'frozen'},generated_normalized={'cuda':'a','metal':'b'}))
        c.write(auditor/'gpu-package.json',dict(package_id=pinned.AUDITOR))
        phase=b'preserved failed phase';(old/'proof/phases.jsonl').write_bytes(phase)
        claim=root/'claim';c.write(claim,dict(capture=str(old/'proof')))
        claims=[dict(path=str(claim),bytes=claim.stat().st_size,sha256=c.sha(claim.read_bytes()))]
        identity=dict(schema=1,provider=linked.PROVIDER,artifact='cubin',source_closure=manifest['golden']['source_sha256'],generated_normalized=manifest['golden']['generated_normalized'])
        receipt=dict(identity=identity,key=linked.key(identity),enabled=True,reused=True,artifact_bytes=3,artifact_sha256=c.sha(b'elf'))
        record=dict(schema=origin.MODE,original_package_id=origin.OWNER,golden=manifest['golden'],native_admission_revalidated=True,input_count=1,native_cases=1,claims_modified=False,
                    original_stage_passed=False,execution_permitted=False,gpu_calls=0,compiler_calls=0,native_calls=0,native_events=[],claims=claims,
                    original_failure_sha256=c.sha(phase),linked_receipt=receipt,linked_artifact=str(root/'saved.cubin'))
        c.write(capture/'origin.json',record)
        c.write(capture/'result.json',dict(mode=origin.MODE,package_id=pinned.AUDITOR,passed=True,containment_verified=True,native_admission_revalidated=True,execution_permitted=False,calculation_verified=False,gpu_calls=0,compiler_calls=0,native_calls=0))
        c.write(capture/'execution.json',dict(passed=True,timed_out=False,child_exit_code=0,final_child_exit_code=0,below_normal_priority=True,timeout_seconds=180))
        c.write(capture/'run.json',dict(source_package=str(root/'failed-package'),source_capture=str(old)))
        c.write(capture/'job.json',{});(capture/'phases.jsonl').write_text('')
        c.write(capture/'artifacts.json',dict(files=c.file_records(capture,['origin.json','result.json','execution.json','run.json','job.json','phases.jsonl'])))
        cli=SimpleNamespace(sha=c.sha,load=c.load,file_records=c.file_records,check_records=c.check_records,job_contained=lambda *a,**k:(True,77),SUITES={'frozen':{'native':1}},forbid_gpu=contextlib.nullcontext)
        return cli,manifest,auditor,capture,receipt

    def prepare(self,root):
        cli,m,owner,capture,receipt=self.fixture(root)
        with patch('portable_continuation_package.owner_snapshot',return_value=dict(manifest=dict(package_id=pinned.AUDITOR,golden=m['golden']))) as snapshot,patch.object(origin,'failure_trace') as failure,patch.object(linked,'read_verified',return_value=(b'elf',receipt)) as read:
            state=pinned.prepare(cli,m,owner,capture,generated_cuda_source=root/'current.cu')
            self.assertEqual(snapshot.call_count,1);self.assertEqual(failure.call_count,1);read.assert_called_once_with(receipt,root/'current.cu',state['linked_artifact'])
        return cli,m,state

    def test_cpu_preparation_binds_all_audit_anchors_without_permitting_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            cli,m,state=self.prepare(Path(tmp))
            self.assertTrue(pinned.check(cli,m,state));self.assertFalse(state['execution_permitted']);self.assertFalse(state['native_values_reused'])

    def test_changed_claim_origin_or_omitted_anchor_is_not_a_fast_hit(self):
        for kind in ('claim','origin','anchors','golden','source'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                cli,m,state=self.prepare(Path(tmp))
                if kind=='claim':Path(state['claims'][0]['path']).write_bytes(b'changed')
                elif kind=='origin':(Path(state['source_capture'])/'origin.json').write_text('{}')
                elif kind=='anchors':state['capture_records']=[]
                elif kind=='golden':m['golden']['source_sha256']={'different':'source'}
                else:state['linked_receipt']['identity']['source_closure']={'different':'source'}
                with self.assertRaises(ValueError):pinned.check(cli,m,state)

    def test_provider_checks_exact_source_headers_and_image_once_without_producer_reaudit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cli,m,state=self.prepare(root);capture=root/'gpu';capture.mkdir();events=[]
            j=SimpleNamespace(invoke=lambda stage,fn,*a:fn(*a),emit=lambda *a,**k:events.append((a,k)))
            with patch.object(linked,'read_verified',return_value=(b'elf',state['linked_receipt'])) as read,patch.object(c,'saved_linked_admission',side_effect=AssertionError('Producer recursion forbidden')):
                with pinned.provider(cli,m,state,capture,j):
                    image,receipt=backend.compile_cuda_source(root/'current.cu',artifact_kind='cubin')
                    with self.assertRaisesRegex(RuntimeError,'fallback'):backend.compile_cuda_artifact()
                read.assert_called_once_with(state['linked_receipt'],root/'current.cu',state['linked_artifact'])
            self.assertEqual(image,b'elf');self.assertEqual((capture/'compiled.cubin').read_bytes(),image)
            self.assertEqual(events[0][0],(linked.STAGE,'verified'))

    def test_missing_activation_and_second_activation_fail_and_restore_backend(self):
        original=backend.compile_cuda_source
        for kind in ('zero','twice'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);cli,m,state=self.prepare(root);capture=root/'gpu';capture.mkdir()
                j=SimpleNamespace(invoke=lambda stage,fn,*a:fn(*a),emit=lambda *a,**k:None)
                with patch.object(linked,'read_verified',return_value=(b'elf',state['linked_receipt'])),self.assertRaises(ValueError):
                    with pinned.provider(cli,m,state,capture,j):
                        if kind=='twice':
                            backend.compile_cuda_source(root/'source.cu');backend.compile_cuda_source(root/'source.cu')
            self.assertIs(backend.compile_cuda_source,original)

    def test_image_failure_propagates_without_fallback_or_publishing_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cli,m,state=self.prepare(root);capture=root/'gpu';capture.mkdir()
            j=SimpleNamespace(invoke=lambda stage,fn,*a:fn(*a),emit=lambda *a,**k:None)
            with patch.object(linked,'read_verified',side_effect=ValueError('Image changed')),self.assertRaisesRegex(ValueError,'Image changed'):
                with pinned.provider(cli,m,state,capture,j):backend.compile_cuda_source(root/'source.cu')
            self.assertFalse((capture/'compiled.cubin').exists())


if __name__=='__main__':unittest.main()
