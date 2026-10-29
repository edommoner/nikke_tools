"""Saved CUDA audits cannot claim fresh native proof or tolerate mutated claims."""
import contextlib,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import portable_partitioned_envelope as envelope
import portable_partitioned_cuda_owner as owner
import portable_partitioned_cuda_trace as trace
import portable_partitioned_cuda_origin as origin
import portable_partitioned_addresses as addresses
import portable_partitioned_transport as transport
import portable_partitioned_witness as witness
import portable_linked_artifact as linked
import windows_validation_observer as observer
from test_portable_partitioned_cuda_receipt import c


class EnvelopeTests(unittest.TestCase):
    def fixture(self,root):
        root=root.resolve()
        capture=root/'gpu';prepared=root/'prepared';capture.mkdir();prepared.mkdir()
        packed=b'input';(prepared/'input.bin').write_bytes(packed)
        m=dict(package_id='source',suite='frozen',golden=dict(input_sha256=c.sha(packed),entries=[dict(name='one')],
            source_sha256={'gpu':'unchanged'},generated_normalized={'cuda':c.sha(b'cu'),'metal':c.sha(b'metal')}),partitioned_cuda_execution=dict(schema='current'))
        context=dict(nonce='nonce',input=dict(input_words=1));state=dict(linked_receipt=dict(key='loaded'))
        claim=dict(package_id='source',prepared=str(prepared),capture=str(capture),nonce='nonce')
        c.write(root/owner.CLAIM,claim);c.write(root/'ledger.json',claim)
        c.write(capture/'run.json',dict(mode='current',stage='gpu',package_id='source',prepared=str(prepared)))
        c.write(capture/'result.json',dict(passed=True,gpu_execution_verified=True,stage_protocol_verified=True,preservation_verified=False))
        c.write(capture/'execution.json',dict(passed=True,timed_out=False,child_exit_code=0,final_child_exit_code=0,below_normal_priority=True))
        layout=dict(output_bytes=1,input_count=1,batches=[dict(cases=1)])
        p=capture/'readback.bin.batches';p.mkdir();c.write(p/'plan.json',layout)
        view=dict(raw_joined_output_sha256='raw',logical_view_sha256='logical',input_count=1)
        evidence=dict(backend='cuda',source_sha256=m['golden']['source_sha256'],input_sha256=c.sha(packed),plan=layout,dispatches=[],
            generated_sha256={'cuda':c.sha(b'cu'),'metal':c.sha(b'metal')},output_sha256='raw',address_view=view)
        c.write(capture/'evidence.json',evidence)
        generation=dict(generated_normalized=m['golden']['generated_normalized'],generation=dict(artifacts={}))
        for k,s in (('cuda','cu'),('metal','metal')):
            (capture/('generated.'+s)).write_bytes(s.encode());generation['generation']['artifacts'][k]=dict(bytes=len(s),sha256=c.sha(s.encode()))
        c.write(prepared/'generation.json',generation)
        (capture/'phases.jsonl').write_text(json.dumps(dict(stage='receipt',receipt=state['linked_receipt']))+'\n')
        comparison=dict(missing_existing_processes=[])
        c.write(capture/'observation.json',dict(before={},after={},comparison=comparison))
        c.write(capture/'artifacts.json',dict(files=[]))
        cli=SimpleNamespace(ROOT=root,load=c.load,sha=c.sha,file_records=c.file_records,check_records=c.check_records,
            SUITES={'frozen':{}},job_contained=lambda *a,**k:(True,77),transport_input_receipt=lambda *a:context['input'],
            open_suite=lambda m:SimpleNamespace(cross=SimpleNamespace(normalized=c.sha)),
            environment_preserved=lambda *a:False,verify_package=lambda p:m)
        stack=contextlib.ExitStack()
        patches=[(origin,'gpu_forbidden',lambda _:contextlib.nullcontext()),(owner,'manifest',lambda _: (m,{})),
            (owner,'prepared',lambda *a:(context,state)),(owner,'ledger',lambda *a:root/'ledger.json'),
            (trace,'verify',lambda *a,**k:True),(addresses,'check_source',lambda *a:None),
            (addresses,'view_file',lambda *a:dict(view)),(transport,'plan',lambda *a,**k:layout),
            (linked,'valid_marker',lambda row:row['stage']=='receipt'),(linked,'read_verified',lambda *a:(b'image',state['linked_receipt'])),
            (witness,'bind_summary',lambda *a:dict(input_count=1,native_reference_cases=1)),
            (observer,'compare_snapshots',lambda *a:comparison)]
        for mod,name,value in patches:stack.enter_context(patch.object(mod,name,value))
        self.addCleanup(stack.close)
        cli.SUITES['frozen']['source']='gpu/entry.slang'
        return cli,capture,prepared,m,comparison

    def test_success_observes_original_envelope_but_leaves_native_and_environment_unproven(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cli,capture,_,_,_=self.fixture(root)
            r=envelope.inspect_current(cli,root,capture,b'peer')
            self.assertTrue(r['original_capture_observed']);self.assertTrue(r['original_process_preserved'])
            self.assertFalse(r['original_environment_preservation_verified']);self.assertFalse(r['calculation_verified'])
            self.assertTrue(r['pending_native_witness_join']);self.assertFalse(r['original_claims_modified'])
            self.assertEqual((r['gpu_calls'],r['compiler_calls'],r['fresh_native_calls']),(0,0,0))

    def test_changed_claim_input_image_record_trace_or_preservation_never_passes(self):
        for kind in ('claim','input','generation','trace','preservation','process','terminal'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);cli,capture,prepared,_,comparison=self.fixture(root)
                if kind=='claim':c.write(root/'ledger.json',{})
                elif kind=='input':(prepared/'input.bin').write_bytes(b'changed')
                elif kind=='generation':(capture/'generated.metal').write_bytes(b'changed')
                elif kind=='trace':trace.verify=lambda *a,**k:False
                elif kind=='preservation':cli.environment_preserved=lambda *a:True
                elif kind=='process':comparison['missing_existing_processes']=['missing']
                else:c.write(capture/'execution.json',dict(passed=True,timed_out=True))
                with self.assertRaises(ValueError):envelope.inspect_current(cli,root,capture,b'peer')

    def test_wrong_platform_and_invalid_budget_stop_before_source_access(self):
        with patch.object(envelope.os,'name','nt'):
            for budget in (0,181,True):
                with self.assertRaises(ValueError):envelope.run(None,None,None,None,None,budget)
        with patch.object(envelope.os,'name','posix'):
            with self.assertRaises(ValueError):envelope.run(None,None,None,None,None,180)


if __name__=='__main__':unittest.main()
