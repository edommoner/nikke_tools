"""Explicit full-source CUBIN reuse, no live compiler and no GPU in these tests."""
import copy,json,os,sys,tempfile,time,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_linked_artifact as saved
import test_portable_device_linker as linker
import portable_backend as backend
from portable_phase_audit import Journal,verify_cuda_trace
cli=linker.cli


class LinkedArtifactTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve();self.capture=self.root/'battle';self.capture.mkdir()
        self.header=self.root/'prelude.h';self.header.write_bytes(b'fixed prelude')
        self.source=self.root/'generated.cu';self.source.write_text('#include "'+str(self.header)+'"\n// shared CUDA\n')
        self.image=self.root/'jit-linked.cubin';self.image.write_bytes(linker.cubin())
        self.golden=dict(source_sha256={'gpu/runtime.slang':'1'*64},generated_normalized={'cuda':'2'*64,'metal':'3'*64})
        self.current=dict(package_id='battle',purpose='sealed',suite='heal-share-rosters',golden=copy.deepcopy(self.golden))
        self.linked=dict(package_id='full',purpose='compiler-diagnostic',suite='compiler-full',golden=copy.deepcopy(self.golden))
        self.producer=dict(source_sha256=self.golden['source_sha256'],generated_normalized=self.golden['generated_normalized'],producer_package_id='full',cuda_sha256=saved.digest(self.source.read_bytes()))
        identity=dict(schema=1,artifact='ptx',source_sha256=self.producer['cuda_sha256'],headers={str(self.header):saved.digest(self.header.read_bytes())},compiler_files={'nvrtc.dll':'4'*64},options=['fixed'])
        self.compiler=dict(source_sha256=self.golden['source_sha256'],generated_normalized=self.golden['generated_normalized'],generated_sha256=dict(cuda=self.producer['cuda_sha256']),compile_artifact=dict(identity=identity,key=saved.key(identity)))
        identity=dict(provider='diagnostic-nvjitlink',artifact='diagnostic-jit-linked-cubin',options=['-arch=sm_86','-verbose'])
        self.link=dict(identity=identity,key=saved.key(identity),artifact=dict(bytes=len(self.image.read_bytes()),sha256=saved.digest(self.image.read_bytes())))
        self.anchors=dict(package_id='full',manifest_sha256='5'*64,artifacts_sha256='6'*64,claim_sha256='7'*64,link_receipt_key=self.link['key'])
    def receipt(self):return saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors)
    def state(self):return dict(receipt=self.receipt(),artifact=str(self.image))
    def request(self):cli.write(self.capture/'linked-artifact-request.json',dict(package='full',capture='link'))

    def sealed_source(self):
        self.current['golden'].update(entries=[dict(name='original-battle')],input_sha256='8'*64,output_sha256='9'*64)
        source=dict(package_id='source-owner',purpose='sealed',suite='moving-group-cache-only',golden=copy.deepcopy(self.current['golden']))
        self.linked.update(package_id='link-controller',purpose='sealed',suite='moving-many-cache-only',golden=dict(source_sha256={'different-controller-source':'0'*64}))
        self.producer.update(producer_package_id=source['package_id'],producer_manifest_sha256='a'*64)
        self.link['identity']['origin']=dict(object_receipt=dict(identity=dict(origin=dict(producer=copy.deepcopy(self.producer)))))
        self.link['key']=saved.key(self.link['identity'])
        self.anchors.update(package_id=self.linked['package_id'],link_receipt_key=self.link['key'],producer_manifest_sha256=self.producer['producer_manifest_sha256'])
        return source

    def test_sealed_source_and_link_controller_have_distinct_bound_owners(self):
        source=self.sealed_source()
        receipt=saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors,sealed_producer=source)
        self.assertEqual(receipt['identity']['sealed_battle_producer']['package_id'],'source-owner')
        self.assertEqual(receipt['identity']['anchors']['package_id'],'link-controller')
        self.assertEqual(saved.read_verified(receipt,self.source,self.image)[0],linker.cubin())
        with self.assertRaisesRegex(ValueError,'full compiler'):self.receipt()

    def ptx_reuse(self):
        source=self.sealed_source();raw=b'.version 8.4\n.target sm_86\n.address_size 64\n'
        self.producer['ptx']=dict(version='8.4',target='sm_86',bytes=len(raw),sha256=saved.digest(raw))
        self.compiler['compile_artifact'].update(artifact_bytes=len(raw),artifact_sha256=saved.digest(raw),hit=True)
        original=copy.deepcopy(self.producer);original['producer_package_id']='original-source'
        original['source_sha256']={'gpu/old-source.slang':'b'*64}
        original_compiler=copy.deepcopy(self.compiler);original_compiler['source_sha256']=original['source_sha256'];original_compiler['compile_artifact']['hit']=False
        self.link['identity']['origin']['object_receipt']['identity']['origin']['producer']=copy.deepcopy(original)
        self.link['key']=saved.key(self.link['identity']);self.anchors['link_receipt_key']=self.link['key']
        return source,(original,original_compiler,raw,raw)

    def test_actual_ptx_and_full_compiler_equality_reuse_old_image_without_relabeling(self):
        source,reuse=self.ptx_reuse()
        receipt=saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors,sealed_producer=source,ptx_reuse=reuse)
        bridge=receipt['identity']['exact_ptx_reuse']
        self.assertEqual(bridge['original_producer']['producer_package_id'],'original-source')
        self.assertEqual(bridge['current_producer']['producer_package_id'],'source-owner')
        self.assertEqual(receipt['identity']['link_identity'],self.link['identity'])
        self.assertEqual(receipt['identity']['source_closure'],self.current['golden']['source_sha256'])
        self.assertEqual(saved.read_verified(receipt,self.source,self.image)[0],linker.cubin())
        with self.assertRaisesRegex(ValueError,'linked object producer'):
            saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors,sealed_producer=source)

    def test_ptx_reuse_rejects_bytes_identity_metadata_and_native_contract_changes(self):
        source,reuse=self.ptx_reuse();old,compiler,raw,_=reuse
        variants=[(old,compiler,raw,raw+b' '),(old,compiler,b'',b''),(old,compiler,bytearray(raw),raw)]
        altered=copy.deepcopy(compiler);altered['compile_artifact']['identity']['options']=['different'];altered['compile_artifact']['key']=saved.key(altered['compile_artifact']['identity']);variants.append((old,altered,raw,raw))
        altered=copy.deepcopy(compiler);altered['compile_artifact']['artifact_sha256']='0'*64;variants.append((old,altered,raw,raw))
        altered=copy.deepcopy(old);altered['ptx']['bytes']+=1;variants.append((altered,compiler,raw,raw))
        for bad in variants:
            with self.assertRaises(ValueError):saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors,sealed_producer=source,ptx_reuse=bad)
        with self.assertRaisesRegex(ValueError,'sealed producer'):
            saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors,ptx_reuse=reuse)
        source['golden']['input_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'independently sealed'):
            saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors,sealed_producer=source,ptx_reuse=reuse)

    def test_reuse_audit_only_writes_new_receipt_and_never_launches_gpu(self):
        source,reuse=self.ptx_reuse();receipt=saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors,sealed_producer=source,ptx_reuse=reuse)
        out=self.root/'reuse-audit.json';before=self.image.read_bytes()
        request={k:str(self.root/k) for k in ('package','capture','producer_package','producer_capture')}
        with patch.object(cli,'verify_package',return_value=self.current),patch.object(cli,'saved_linked_admission',return_value=dict(receipt=receipt)),patch.object(cli,'run_capture',side_effect=AssertionError('No GPU')):
            result=cli.linked_reuse_audit(request,out)
            self.assertTrue(result['reuse_admission_verified']);self.assertFalse(result['calculation_verified'])
            self.assertEqual(result['gpu_calls'],0);self.assertEqual(result['compiler_calls'],0)
            with self.assertRaises(FileExistsError):cli.linked_reuse_audit(request,out)
            with self.assertRaisesRegex(ValueError,'immutable inputs'):cli.linked_reuse_audit(request,Path(request['capture'])/'new.json')
            with self.assertRaisesRegex(ValueError,'Exact absolute'):cli.linked_reuse_audit({},self.root/'missing.json')
        self.assertEqual(self.image.read_bytes(),before)

    def test_controller_reuse_audits_both_producers_and_checks_current_claim(self):
        source,reuse=self.ptx_reuse();old,old_compiler,old_raw,current_raw=reuse
        package=self.root/'reuse-link-owner';package.mkdir();capture=self.root/'reuse-link';capture.mkdir()
        obj=self.root/'reuse-object';obj.mkdir();prior=self.root/'prior-ptx';prior.mkdir()
        current_package=self.root/'current-package';current_package.mkdir();current_capture=self.root/'current-ptx';current_capture.mkdir()
        cli.write(package/'gpu-package.json',self.linked);cli.write(current_package/'gpu-package.json',source)
        self.producer['producer_manifest_sha256']=saved.digest((current_package/'gpu-package.json').read_bytes())
        self.producer['producer_artifacts_sha256']='c'*64
        cli.write(current_package/'compile-claimed-cuda.json',dict(package_id=source['package_id'],capture=str(current_capture),artifact_kind='ptx'))
        for p in (package/'jit-link-object-claimed-cuda.json',capture/'artifacts.json'):cli.write(p,{})
        cli.write(capture/'object-request.json',dict(object_capture=str(obj)))
        cli.write(obj/'object-request.json',dict(source_capture=str(prior),source_package=str(self.root/'old-package')))
        cli.write(prior/'compiler.json',old_compiler);(prior/'compiled.ptx').write_bytes(old_raw)
        cli.write(current_capture/'compiler.json',self.compiler)
        cli.write(capture/'jit-link.json',dict(origin=self.link['identity']['origin'],receipt=self.link))
        from windows_validation_observer import compare_snapshots
        before=dict(processes=[],service_status='unverified');cli.write(capture/'observation.json',dict(before=before,after=before,comparison=compare_snapshots(before,before)))
        request=dict(package=str(package),capture=str(capture),producer_package=str(current_package),producer_capture=str(current_capture))
        def verify(path,**kw):return self.linked if path==package else source
        with patch.object(cli,'verify_package',side_effect=verify),patch.object(cli,'audit_jit_link_capture',return_value=dict(link_verified=True,containment_verified=True)) as audit,patch.object(cli,'assembly_origin',return_value=(self.producer,current_raw)) as origin:
            state=cli.saved_linked_admission(self.current,request)
            audit.assert_called_once_with(self.linked,capture,package_root=package)
            origin.assert_called_once_with(self.current,current_package,current_capture,sealed_battle_source=True)
            self.assertEqual(state['receipt']['identity']['exact_ptx_reuse']['original_producer'],old)
            self.assertEqual(state['receipt']['identity']['exact_ptx_reuse']['current_producer'],self.producer)
            cli.write(current_package/'compile-claimed-cuda.json',dict(package_id='wrong',capture=str(current_capture),artifact_kind='ptx'))
            with self.assertRaisesRegex(ValueError,'claim mismatch'):cli.saved_linked_admission(self.current,request)
            with self.assertRaisesRegex(ValueError,'Both current PTX'):cli.saved_linked_admission(self.current,{k:v for k,v in request.items() if k!='producer_capture'})

    def test_cli_reuse_audit_forwards_explicit_paths_without_execution(self):
        import contextlib,io
        proof=dict(schema='linked-ptx-reuse-audit-v1',package_id='receiver',reuse_admission_verified=True,
                   calculation_verified=False,gpu_calls=0,compiler_calls=0,native_battle_calls=0,
                   original_artifacts_modified=False,scope='fixture',receipt=dict(key='d'*64))
        paths={k:self.root/k for k in ('linked-package','linked-capture','producer-package','producer-capture','out')}
        args=['linked-reuse-audit',*[v for k,p in paths.items() for v in ('--'+k,str(p))]]
        with patch.object(cli,'linked_reuse_audit',return_value=proof) as audit,contextlib.redirect_stdout(io.StringIO()) as stdout:
            cli.main(args)
        self.assertEqual(audit.call_args.args[0],dict(package=str(paths['linked-package']),capture=str(paths['linked-capture']),producer_package=str(paths['producer-package']),producer_capture=str(paths['producer-capture'])))
        self.assertEqual(audit.call_args.args[1],paths['out'])
        result=json.loads(stdout.getvalue());self.assertFalse(result['calculation_verified']);self.assertEqual(result['receipt_key'],'d'*64)

    def test_run_and_staged_cli_forward_current_producer_without_bypassing_transaction(self):
        import contextlib,io
        for command in ('run','staged-run'):
            args=[command,'--backend','cuda','--capture',str(self.capture),'--linked-package',str(self.root/'link'),'--linked-capture',str(self.root/'proof'),'--linked-producer-package',str(self.root/'producer'),'--linked-producer-capture',str(self.root/'compile')]
            if command=='staged-run':args+=['--transaction',str(self.root/'transaction')]
            with patch.object(cli,'run_capture',return_value=dict(calculation_verified=True)) as run,contextlib.redirect_stdout(io.StringIO()):cli.main(args)
            self.assertEqual(run.call_args.kwargs['linked_producer_package'],self.root/'producer')
            self.assertEqual(run.call_args.kwargs['linked_producer_capture'],self.root/'compile')
            if command=='staged-run':self.assertEqual(run.call_args.kwargs['preflight_transaction'],self.root/'transaction')
            with patch.object(cli,'run_capture',side_effect=AssertionError('No execution')),self.assertRaisesRegex(ValueError,'both paths'):
                cli.main(args[:args.index('--linked-producer-capture')]+(args[args.index('--transaction'):] if command=='staged-run' else []))

    def test_sealed_source_admission_rejects_changed_native_baseline_and_provenance(self):
        source=self.sealed_source()
        changes=[(source,'purpose','development'),(self.linked,'purpose','compiler-diagnostic'),(source,'package_id','wrong-owner'),(source,'selected_cases',['partial']),
                 (source['golden'],'input_sha256','0'*64),(source['golden'],'output_sha256','0'*64),(source['golden'],'entries',[]),
                 (self.anchors,'producer_manifest_sha256','0'*64),(self.anchors,'package_id','wrong-controller'),(self.anchors,'link_receipt_key','0'*64),
                 (self.link['identity']['origin']['object_receipt']['identity']['origin'],'producer',{})]
        for obj,key,value in changes:
            existed=key in obj;old=copy.deepcopy(obj.get(key));obj[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                saved.admission(self.current,self.linked,self.producer,self.compiler,self.link,self.anchors,sealed_producer=source)
            if existed:obj[key]=old
            else:obj.pop(key)

    def test_sealed_controller_reads_and_binds_original_source_manifest(self):
        source=self.sealed_source()
        package=self.root/'package';package.mkdir();link_capture=self.root/'link';link_capture.mkdir();object_capture=self.root/'object';object_capture.mkdir();producer_capture=self.root/'producer';producer_capture.mkdir();source_package=self.root/'source-package';source_package.mkdir()
        cli.write(package/'gpu-package.json',self.linked);cli.write(source_package/'gpu-package.json',source)
        self.producer['producer_manifest_sha256']=saved.digest((source_package/'gpu-package.json').read_bytes())
        self.link['identity']['origin']['object_receipt']['identity']['origin']['producer']=copy.deepcopy(self.producer)
        self.link['key']=saved.key(self.link['identity'])
        for p in (package/'jit-link-object-claimed-cuda.json',link_capture/'artifacts.json'):cli.write(p,{})
        cli.write(link_capture/'object-request.json',dict(object_capture=str(object_capture)))
        cli.write(object_capture/'object-request.json',dict(source_capture=str(producer_capture),source_package=str(source_package)))
        cli.write(producer_capture/'compiler.json',self.compiler)
        cli.write(link_capture/'jit-link.json',dict(origin=self.link['identity']['origin'],receipt=self.link))
        from windows_validation_observer import compare_snapshots
        before=dict(processes=[],service_status='unverified');cli.write(link_capture/'observation.json',dict(before=before,after=before,comparison=compare_snapshots(before,before)))
        def verify(path,**kw):return self.linked if path==package else source
        with patch.object(cli,'verify_package',side_effect=verify) as verify_call,patch.object(cli,'audit_jit_link_capture',return_value=dict(link_verified=True,containment_verified=True)):
            state=cli.saved_linked_admission(self.current,dict(package=str(package),capture=str(link_capture)))
            self.assertEqual(state['receipt']['identity']['sealed_battle_producer']['manifest_sha256'],self.producer['producer_manifest_sha256'])
            self.assertEqual(verify_call.call_args_list[-1].args,(source_package,))
            source['suite']='compiler-commands'
            with self.assertRaisesRegex(ValueError,'sealed world battle'):cli.saved_linked_admission(self.current,dict(package=str(package),capture=str(link_capture)))
    def test_registered_full_world_family_uses_same_exact_source_admission(self):
        self.linked['suite']='compiler-full--max-ammo-scaling-retention'
        self.linked['golden']['baseline_suite']='max-ammo-scaling-retention'
        self.assertEqual(self.receipt()['identity']['provider'],saved.PROVIDER)
        self.linked['golden']['baseline_suite']='other'
        with self.assertRaisesRegex(ValueError,'full compiler'):self.receipt()
    def test_exact_source_and_header_reuse_returns_distinct_toolchain_identity(self):
        r=self.receipt();image,actual=saved.read_verified(r,self.source,self.image)
        self.assertEqual(image,linker.cubin());self.assertEqual(actual,r);self.assertEqual(r['identity']['provider'],saved.PROVIDER);self.assertNotIn('hit',r)
        self.assertNotEqual(r['key'],self.compiler['compile_artifact']['key'])
    def test_commands_development_or_changed_source_baseline_never_admit(self):
        for obj,field,value in ((self.current,'purpose','development'),(self.linked,'suite','compiler-commands'),(self.producer,'producer_package_id','other')):
            old=obj[field];obj[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.receipt()
            obj[field]=old
        for obj,field in ((self.producer,'source_sha256'),(self.compiler,'generated_normalized'),(self.linked['golden'],'source_sha256')):
            old=obj[field];obj[field]={}
            with self.subTest(field=field),self.assertRaises(ValueError):self.receipt()
            obj[field]=old
    def test_changed_cuda_header_or_image_rejects_reuse(self):
        r=self.receipt()
        for path,value,reason in ((self.source,b'changed','exact CUDA'),(self.header,b'changed','header'),(self.image,linker.cubin()+b'changed','artifact changed')):
            old=path.read_bytes();path.write_bytes(value)
            with self.subTest(reason=reason),self.assertRaisesRegex(ValueError,reason):saved.read_verified(r,self.source,self.image)
            path.write_bytes(old)
    def test_compiler_or_link_key_tampering_rejects_admission(self):
        for obj in (self.compiler['compile_artifact'],self.link):
            old=obj['key'];obj['key']='0'*64
            with self.assertRaisesRegex(ValueError,'key|identity'):self.receipt()
            obj['key']=old
    def test_cli_provider_reuses_image_without_calling_nvrtc_and_restores_backend(self):
        self.request();original=backend.compile_cuda_source;j=Journal(self.capture/'phases.jsonl')
        with patch.object(cli,'saved_linked_admission',return_value=self.state()),patch.dict(os.environ,NIKKE_CUDA_ARTIFACT='cubin'),cli.saved_linked_provider(self.current,self.capture,'cuda',j) as admitted:
            self.assertEqual(admitted,self.receipt())
            self.assertEqual(backend.compile_cuda_source(self.source)[0],linker.cubin())
            with self.assertRaisesRegex(RuntimeError,'forbidden'):backend.compile_cuda_artifact(None,b'',[])
            with self.assertRaisesRegex(ValueError,'One explicit'):backend.compile_cuda_source(self.source)
        self.assertIs(backend.compile_cuda_source,original)
        rows=[json.loads(s) for s in (self.capture/'phases.jsonl').read_text().splitlines()]
        self.assertEqual([(r['stage'],r['state']) for r in rows],[('cuda_linked_origin','verified'),('cuda_linked_artifact','entered'),('cuda_linked_artifact','returned'),(saved.STAGE,'verified'),('cuda_live_compile_forbidden','rejected')])
    def test_source_change_under_provider_stops_before_image_receipt(self):
        self.request();state=self.state();self.source.write_bytes(b'wrong current CUDA')
        with patch.object(cli,'saved_linked_admission',return_value=state),patch.dict(os.environ,NIKKE_CUDA_ARTIFACT='cubin'),cli.saved_linked_provider(self.current,self.capture,'cuda',Journal(self.capture/'phases.jsonl')):
            with self.assertRaisesRegex(ValueError,'exact CUDA'):backend.compile_cuda_source(self.source)
        rows=[json.loads(s) for s in (self.capture/'phases.jsonl').read_text().splitlines()];self.assertFalse(any(saved.valid_marker(r) for r in rows))
    def test_provider_rejects_metal_and_missing_pair_or_smoke_before_job(self):
        self.request()
        with self.assertRaises(ValueError):
            with cli.saved_linked_provider(self.current,self.capture,'metal',Journal(self.capture/'phases.jsonl')):pass
        with patch.object(cli,'verify_package',return_value=self.current),patch.object(cli,'run_job',side_effect=AssertionError('No job')):
            for kwargs in (dict(linked_package=self.root),dict(linked_package=self.root,linked_capture=self.root,smoke=True),dict(linked_package=self.root,linked_capture=self.root,cpu_only=True),dict(linked_package=self.root,linked_capture=self.root)):
                with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):cli.run_capture(self.root/'blocked','cuda',61,self.root,**kwargs)
        self.assertFalse((self.root/'blocked').exists())
    def trace(self):
        rows=[dict(stage=saved.STAGE,state='verified',receipt=self.receipt())]
        for stage in ('cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2'):rows.extend([dict(stage=stage,state='entered'),dict(stage=stage,state='returned',return_code=0)])
        return [dict(r,pid=17,monotonic_ns=i,wall_time_ns=i) for i,r in enumerate(rows)]
    def test_trace_accepts_distinct_saved_marker_and_rejects_tampering_or_mixed_compilers(self):
        rows=self.trace();self.assertTrue(verify_cuda_trace(rows,pid=17));self.assertFalse(verify_cuda_trace(rows[1:],pid=17))
        bad=copy.deepcopy(rows);bad[0]['receipt']['key']='0'*64;self.assertFalse(verify_cuda_trace(bad,pid=17))
        bad=copy.deepcopy(rows);bad.insert(0,dict(stage='nvrtcCompileProgram',state='entered',pid=17,monotonic_ns=-1));self.assertFalse(verify_cuda_trace(bad,pid=17))
    def test_independent_audit_checks_saved_origin_image_budget_and_forbidden_live_compile(self):
        self.request();state=self.state();self.source.replace(self.capture/'generated.cu');(self.capture/'compiled.cubin').write_bytes(self.image.read_bytes());cli.write(self.capture/'execution.json',dict(timeout_seconds=60))
        rows=[dict(stage='cuda_linked_origin',state='verified',receipt=state['receipt']),dict(stage='cuda_linked_artifact',state='entered'),dict(stage='cuda_linked_artifact',state='returned'),dict(stage=saved.STAGE,state='verified',receipt=state['receipt'])]
        def write(): (self.capture/'phases.jsonl').write_text('\n'.join(map(json.dumps,rows))+'\n')
        write()
        with patch.object(cli,'saved_linked_admission',return_value=state):
            self.assertTrue(cli.audit_saved_linked_artifact(self.current,self.capture,state['receipt']))
            rows.append(dict(stage='nvrtcCreateProgram',state='entered'));write()
            with self.assertRaisesRegex(ValueError,'NVRTC'):cli.audit_saved_linked_artifact(self.current,self.capture,state['receipt'])
            rows.pop();write();cli.write(self.capture/'execution.json',dict(timeout_seconds=61))
            with self.assertRaisesRegex(ValueError,'budget'):cli.audit_saved_linked_artifact(self.current,self.capture,state['receipt'])
    def test_streamed_transport_accepts_saved_receipt_without_fake_nvrtc_return(self):
        import test_portable_file_transport as transport
        fixture=transport.FileTransportTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.run_cuda(32);rows=fixture.rows();native=next(r for r in rows if r['stage']=='nvrtcCompileProgram')
        rows=[r for r in rows if r['stage']!='nvrtcCompileProgram']
        rows.insert(0,dict(native,stage=saved.STAGE,state='verified',receipt=self.receipt()))
        self.assertTrue(verify_cuda_trace(rows,pid=os.getpid()))
        rows.pop(0);self.assertFalse(verify_cuda_trace(rows,pid=os.getpid()))
    def test_parent_claim_budget_and_environment_are_shared_with_normal_run(self):
        storage=patch.object(cli,'capture_storage_preflight');budget=storage.start();self.addCleanup(storage.stop)
        result=dict(calculation_verified=False,passed=False);folder=self.root/'parent';env={'UNRELATED':'same'}
        def job(*args,**kwargs):
            self.assertEqual(cli.os.environ['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048');self.assertEqual(cli.os.environ['NIKKE_CUDA_ARTIFACT'],'cubin');return dict(passed=True)
        fake_os=types.SimpleNamespace(**dict(vars(os),name='nt',environ=env))
        with patch.object(cli,'ROOT',self.root),patch.object(cli,'os',fake_os),patch.object(cli,'verify_package',return_value=self.current),patch.object(cli,'saved_linked_admission',return_value=self.state()),patch.object(cli,'cpu_preflight',return_value=dict(passed=True)),patch.object(cli,'cpu_test_groups'),patch.object(cli,'run_job',side_effect=job) as run,patch.object(cli,'copy_generated'),patch.object(cli,'audit_capture',return_value=result):
            self.assertEqual(cli.run_capture(folder,'cuda',60,self.root,linked_package=self.root,linked_capture=self.root),result)
            run.assert_called_once();self.assertTrue((self.root/'gpu-claimed-cuda.json').exists());self.assertTrue((folder/'linked-artifact-request.json').exists())
        self.assertEqual(budget.call_count,2)
        self.assertEqual(env,{'UNRELATED':'same'})

    def test_current_producer_request_is_persisted_for_child_and_post_audit(self):
        folder=self.root/'current-parent';env={'UNRELATED':'same'};result=dict(calculation_verified=False,passed=False)
        fake_os=types.SimpleNamespace(**dict(vars(os),name='nt',environ=env))
        producer=self.root/'current-source';compile_capture=self.root/'current-compile'
        expected=dict(package=str(self.root),capture=str(self.root),producer_package=str(producer),producer_capture=str(compile_capture))
        def job(*args,**kwargs):
            self.assertEqual(cli.load(folder/'linked-artifact-request.json'),expected)
            self.assertEqual(cli.os.environ['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
            return dict(passed=True)
        with patch.object(cli,'ROOT',self.root),patch.object(cli,'os',fake_os),patch.object(cli,'verify_package',return_value=self.current),patch.object(cli,'saved_linked_admission',return_value=self.state()) as admit,patch.object(cli,'cpu_preflight',return_value=dict(passed=True)) as native,patch.object(cli,'cpu_test_groups') as tests,patch.object(cli,'run_job',side_effect=job),patch.object(cli,'capture_storage_preflight'),patch.object(cli,'copy_generated'),patch.object(cli,'audit_capture',return_value=result):
            cli.run_capture(folder,'cuda',60,self.root,linked_package=self.root,linked_capture=self.root,linked_producer_package=producer,linked_producer_capture=compile_capture)
            admit.assert_called_once_with(self.current,expected);native.assert_called_once();tests.assert_called_once()
        self.assertEqual(env,{'UNRELATED':'same'})

    def test_controller_audits_link_package_claim_in_its_own_root_and_checks_observation(self):
        package=self.root/'package';package.mkdir();link_capture=self.root/'link';link_capture.mkdir();object_capture=self.root/'object';object_capture.mkdir();producer_capture=self.root/'producer';producer_capture.mkdir()
        for p in (package/'gpu-package.json',package/'jit-link-object-claimed-cuda.json',link_capture/'artifacts.json'):cli.write(p,{})
        cli.write(link_capture/'object-request.json',dict(object_capture=str(object_capture)))
        cli.write(object_capture/'object-request.json',dict(source_capture=str(producer_capture)))
        cli.write(producer_capture/'compiler.json',self.compiler)
        origin=dict(object_receipt=dict(identity=dict(origin=dict(producer=self.producer))))
        cli.write(link_capture/'jit-link.json',dict(origin=origin,receipt=self.link))
        from windows_validation_observer import compare_snapshots
        before=dict(processes=[],service_status='unverified');observation=dict(before=before,after=before,comparison=compare_snapshots(before,before));cli.write(link_capture/'observation.json',observation)
        with patch.object(cli,'verify_package',return_value=self.linked),patch.object(cli,'audit_jit_link_capture',return_value=dict(link_verified=True,containment_verified=True)) as audit:
            state=cli.saved_linked_admission(self.current,dict(package=str(package),capture=str(link_capture)))
            self.assertEqual(state['receipt']['artifact_sha256'],self.link['artifact']['sha256']);audit.assert_called_once_with(self.linked,link_capture,package_root=package)
            observation['comparison']['missing_existing_processes']=[dict(pid=1)];cli.write(link_capture/'observation.json',observation)
            with self.assertRaisesRegex(ValueError,'observation'):cli.saved_linked_admission(self.current,dict(package=str(package),capture=str(link_capture)))

    def test_cli_saved_arguments_cannot_mix_with_nvrtc_settings(self):
        for flag in ('--require-cache','--artifact-kind'):
            args=['run','--backend','cuda','--capture',str(self.capture),'--linked-package','p','--linked-capture','c',flag]+(['cubin'] if flag=='--artifact-kind' else [])
            with patch.object(cli,'run_capture',side_effect=AssertionError('No launch')),self.assertRaisesRegex(ValueError,'exclusive'):cli.main(args)


if __name__=='__main__':unittest.main()
