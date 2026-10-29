"""New source ownership reuses transport and read-only admission, never retrying v1."""
import contextlib,copy,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import portable_partitioned_cli as capsule
import portable_partitioned_cuda_owner as owner
import portable_partitioned_cuda_receipt as pinned
import portable_linked_artifact as linked
import portable_backend as backend
from test_portable_partitioned_cuda_receipt import c


class CurrentSourceTests(unittest.TestCase):
    def corpus(self):
        config=c.SUITES['coordinate-resident-frames']
        return config,c.load(ROOT/config['golden']),(ROOT/'tests/fixtures/resident-append-full106-metal-v1.json').read_bytes()

    def test_current_seal_rejects_unpinned_proof_or_different_complete_golden(self):
        config,golden,raw=self.corpus()
        good=capsule.current_reference(c,ROOT,config,golden,raw)
        self.assertEqual(good['proof_sha256'],c.sha(raw))
        for kind in ('proof','golden','coverage','native'):
            g=copy.deepcopy(golden);data=json.loads(raw)
            if kind=='proof':data['calculation_verified']=False
            elif kind=='golden':g['entries'][0]['output_sha256']='0'*64
            elif kind=='coverage':data['independent_audit']['groups'].pop()
            else:data['independent_audit']['native_cases']=0
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                capsule.current_reference(c,ROOT,config,g,raw if kind=='golden' else json.dumps(data).encode())

    def test_current_manifest_binds_both_reference_generations_and_the_same_wire_abi(self):
        config,golden,raw=self.corpus()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'research').mkdir()
            for name in [config['golden'],*__import__('portable_partitioned_addresses').SOURCES]:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
            (root/'research/partitioned-current-metal-reference.json').write_bytes(raw)
            physical=(ROOT/'tests/fixtures/partitioned-physical-reference-v1.json').read_bytes()
            (root/'research/partitioned-cuda-native-reference.json').write_bytes(physical)
            m=dict(package_id='current',suite='coordinate-resident-frames',purpose='sealed',golden=golden,
                partitioned_diagnostic=dict(wire_address_profile=__import__('portable_partitioned_addresses').PROFILE),
                partitioned_cuda_execution=dict(schema=capsule.CURRENT,batch_size=16,maximum_gpu_seconds=60,
                    native_reference_sha256=c.sha(physical),prior_physical_reference_reused=True,
                    current_source_reference=capsule.current_reference(c,root,config,golden,raw)))
            cli=SimpleNamespace(ROOT=root,verify_package=lambda _:m,load=c.load,sha=c.sha,SUITES=c.SUITES)
            self.assertEqual(owner.manifest(cli)[0],m)
            for key,value in [('batch_size',1),('maximum_gpu_seconds',61),('prior_physical_reference_reused',False),('native_reference_sha256','0'*64),('current_source_reference',{})]:
                old=m['partitioned_cuda_execution'][key];m['partitioned_cuda_execution'][key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):owner.manifest(cli)
                m['partitioned_cuda_execution'][key]=old
            (root/'research/partitioned-current-metal-reference.json').write_bytes(b'{}')
            with self.assertRaises(ValueError):owner.manifest(cli)

    def state(self,root):
        package=root/'compiler';capture=root/'link'
        package.mkdir();capture.mkdir()
        c.write(package/'gpu-package.json',dict(package_id='producer'))
        c.write(package/'jit-link-object-claimed-cuda.json',dict(capture=str(capture)))
        for name in pinned.CURRENT_CAPTURE:c.write(capture/name,{})
        proof=dict(identity=dict(provider='link'),key='link-key',artifact=dict(bytes=3,sha256=c.sha(b'elf')))
        c.write(capture/'jit-link.json',dict(receipt=proof))
        m=dict(suite='frozen',golden=dict(entries=[dict(name='one')],source_sha256={'gpu':'source'},generated_normalized={'cuda':'a','metal':'b'}))
        anchors=dict(package_id='producer',manifest_sha256=c.sha((package/'gpu-package.json').read_bytes()),
            artifacts_sha256=c.sha((capture/'artifacts.json').read_bytes()),claim_sha256=c.sha((package/'jit-link-object-claimed-cuda.json').read_bytes()),link_receipt_key=proof['key'])
        identity=dict(schema=1,provider=linked.PROVIDER,artifact='cubin',source_closure=m['golden']['source_sha256'],
            generated_normalized=m['golden']['generated_normalized'],link_identity=proof['identity'],anchors=anchors)
        receipt=dict(identity=identity,key=linked.key(identity),enabled=True,reused=True,artifact_bytes=3,artifact_sha256=c.sha(b'elf'))
        audit=Mock(return_value=dict(receipt=receipt,artifact=str(capture/'jit-linked.cubin')))
        cli=SimpleNamespace(sha=c.sha,load=c.load,file_records=c.file_records,check_records=c.check_records,
            SUITES={'frozen':dict(native=1)},forbid_gpu=contextlib.nullcontext,saved_linked_admission=audit)
        with patch.object(linked,'read_verified',return_value=(b'elf',receipt)) as read:
            state=pinned.prepare_current(cli,m,package,capture,generated_cuda_source=root/'current.cu')
            audit.assert_called_once_with(m,dict(package=str(package.resolve()),capture=str(capture.resolve())))
            read.assert_called_once()
        return cli,m,state

    def test_current_cpu_admission_checks_source_link_claim_and_complete_anchors(self):
        for kind in ('valid','claim','missing-anchor','golden','artifact-path','receipt'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);cli,m,state=self.state(root)
                if kind=='valid':self.assertTrue(pinned.check(cli,m,state));continue
                if kind=='claim':(Path(state['linked_root'])/'jit-link-object-claimed-cuda.json').write_bytes(b'{}')
                elif kind=='missing-anchor':state['capture_records'].pop()
                elif kind=='golden':m['golden']['entries'].append(dict(name='extra'))
                elif kind=='artifact-path':state['linked_artifact']=str(root/'other.cubin')
                else:state['linked_receipt']['identity']['source_closure']={'wrong':'source'}
                with self.assertRaises(ValueError):pinned.check(cli,m,state)

    def test_current_gpu_provider_reuses_the_existing_single_activation_and_never_reaudits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cli,m,state=self.state(root);folder=root/'gpu';folder.mkdir()
            j=SimpleNamespace(invoke=lambda _,fn,*a:fn(*a),emit=lambda *a,**k:None)
            cli.saved_linked_admission.side_effect=AssertionError('Heavy producer audit at GPU boundary')
            with patch.object(linked,'read_verified',return_value=(b'elf',state['linked_receipt'])) as read:
                with pinned.provider(cli,m,state,folder,j):
                    self.assertEqual(backend.compile_cuda_source(root/'current.cu',artifact_kind='cubin')[0],b'elf')
                    with self.assertRaisesRegex(RuntimeError,'fallback'):backend.compile_cuda_artifact()
                    with self.assertRaises(ValueError):backend.compile_cuda_source(root/'current.cu',artifact_kind='cubin')
                read.assert_called_once()
            self.assertEqual(cli.saved_linked_admission.call_count,1)

    def test_current_ledger_is_source_bound_and_stable_across_owner_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cli,m,state=self.state(root);cli.ROOT=root/'first'
            first=owner.ledger(cli,state);cli.ROOT=root/'second'
            self.assertEqual(first,owner.ledger(cli,state))
            changed=copy.deepcopy(state);changed['golden_sha256']='other'
            self.assertNotEqual(first,owner.ledger(cli,changed))
            self.assertNotIn(Path(state['source_capture']),first.parents)

    def test_storage_failure_precedes_new_execution_claim_and_job(self):
        import struct
        packed=struct.pack('<3I',1,7,8)
        m=dict(suite='frozen',golden=dict(entries=[{}],input_sha256=c.sha(packed)))
        cli=SimpleNamespace(SUITES={'frozen':dict(input_words=2,output_words=3)})
        with patch('portable_capture_storage.space_status',return_value=dict(passed=False)) as space:
            with self.assertRaisesRegex(RuntimeError,'before CUDA claim'):owner.storage_preflight(cli,m,packed,Path('unused'))
            self.assertEqual(space.call_args.args[1],2*12+len(packed)+64*1024*1024+len(packed))

    def test_current_failed_execution_keeps_its_source_bound_ledger_and_cannot_retry(self):
        for low_space in (False,True):
            with self.subTest(low_space=low_space),tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ):
                root=Path(tmp);cli,m,state=self.state(root);cli.ROOT=root/'owner';cli.ROOT.mkdir()
                m.update(package_id='current',partitioned_cuda_execution=dict(schema=capsule.CURRENT))
                prepared=root/'prepared';prepared.mkdir();(prepared/'input.bin').write_bytes(b'packed')
                context=dict(nonce='unique',settings=dict(slang_root=str(root/'sdk'),generation_cache=str(root/'cache')))
                cli.run_job=Mock(return_value=dict(passed=False));cli.collect=lambda *a:None
                cli.job_contained=lambda *a,**k:(False,None);cli.environment_preserved=lambda *a:False
                original=(Path(state['linked_root'])/'jit-link-object-claimed-cuda.json').read_bytes()
                with patch.object(owner,'os',SimpleNamespace(name='nt',environ=os.environ)),patch.object(owner,'manifest',return_value=(m,{})),patch.object(owner,'prepared',return_value=(context,state)),patch.object(owner,'storage_preflight',side_effect=RuntimeError('disk full') if low_space else None,return_value=dict(passed=True)):
                    if low_space:
                        with self.assertRaisesRegex(RuntimeError,'disk full'):owner.run(cli,'gpu',root/'gpu',root/'workspace',prepare_capture=prepared)
                        self.assertFalse((cli.ROOT/owner.CLAIM).exists());self.assertFalse(owner.ledger(cli,state).exists());cli.run_job.assert_not_called()
                    else:
                        result=owner.run(cli,'gpu',root/'gpu',root/'workspace',prepare_capture=prepared)
                        self.assertFalse(result['passed']);self.assertFalse(result['calculation_verified'])
                        self.assertTrue((cli.ROOT/owner.CLAIM).exists());self.assertTrue(owner.ledger(cli,state).exists())
                        with self.assertRaises(FileExistsError):owner.run(cli,'gpu',root/'another',root/'workspace',prepare_capture=prepared)
                        cli.run_job.assert_called_once()
                self.assertEqual((Path(state['linked_root'])/'jit-link-object-claimed-cuda.json').read_bytes(),original)


if __name__=='__main__':unittest.main()
