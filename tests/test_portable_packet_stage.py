"""Whole-stage orchestration cannot broaden preparation or replay a claim."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('packet_stage',ROOT/'scripts/run-gpu-packet.py');stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
class PacketStageTests(unittest.TestCase):
    def request(self,mode,base):
        return {key:('a'*64 if key=='object_sha256' else str((base/key).resolve())) for key in stage.OBJECT_STAGES[mode]}
    def test_saved_linked_battle_uses_existing_run_and_fixed_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);request={key:str((base/key).resolve()) for key in stage.LINKED_FIELDS}
            plan=stage.recipe('id','gpu-linked','cuda',base/'capture',base/'original',90,request)
            args=stage.proof_arguments(plan)
            self.assertEqual(args,['run','--backend','cuda','--capture',plan['proof_capture'],'--timeout','60',
                '--linked-package',request['linked_package'],'--linked-capture',request['linked_capture'],
                '--original-workspace',plan['original_workspace']])
            self.assertEqual(plan['memory_limit_mb'],2048)
            for bad in (None,{},dict(request,extra='--gpu'),dict(request,linked_capture='relative'),dict(request,linked_package=True)):
                with self.subTest(bad=bad),self.assertRaises(ValueError):
                    stage.recipe('id','gpu-linked','cuda',base/'capture',base/'original',90,bad)
            with self.assertRaisesRegex(ValueError,'CUDA backend'):stage.recipe('id','gpu-linked','metal',base/'capture',base/'original',90,request)
            with self.assertRaisesRegex(ValueError,'original workspace'):stage.recipe('id','gpu-linked','cuda',base/'capture',None,90,request)
    def test_saved_linked_calculation_remains_separate_from_outer_failure(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);root=base/'packet';root.mkdir();folder=base/'stage'
            request={key:str((base/key).resolve()) for key in stage.LINKED_FIELDS}
            def bounded(*args,**kwargs):
                self.assertEqual(kwargs['env']['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
                (folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps(dict(calculation_verified=True,passed=False)))
                return dict(passed=False)
            cli=SimpleNamespace(bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
            with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False):
                result=stage.run_stage(folder,'gpu-linked','cuda',90,base/'original',request)
            self.assertTrue(result['calculation_verified']);self.assertFalse(result['stage_verified'])
            self.assertFalse(result['compiler_verified']);self.assertFalse(result['generation_verified'])
            with self.assertRaises(FileExistsError):
                with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False):
                    stage.run_stage(base/'again','gpu-linked','cuda',90,base/'original',request)
    def test_saved_object_stages_only_forward_exact_paths_to_existing_cli(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            for mode,fields in stage.OBJECT_STAGES.items():
                request=self.request(mode,base)
                p=stage.recipe('id',mode,'cuda',base/'capture',base/'original',180,request)
                arguments=stage.proof_arguments(p)
                if mode=='recover-object':
                    expected=[mode,'--source-package',request['source_package'],'--source-capture',request['source_capture'],'--out',p['proof_capture'],'--object-sha256',request['object_sha256']]
                else:
                    expected=[mode,'--capture',p['proof_capture'],'--timeout','60','--original-workspace',p['original_workspace']]
                    for key in fields:expected.extend(['--'+key.replace('_','-'),request[key]])
                self.assertEqual(arguments,expected);self.assertEqual(p['memory_limit_mb'],2048)
                self.assertNotIn('--candidate',arguments);self.assertNotIn('--ptxas-level',arguments)
                self.assertNotIn('--cpu-only',arguments);self.assertNotIn('run',arguments)
                with self.assertRaisesRegex(ValueError,'CUDA backend'):stage.recipe('id',mode,'metal',base/'capture',base/'original',180,request)
                with self.assertRaisesRegex(ValueError,'original workspace'):stage.recipe('id',mode,'cuda',base/'capture',None,180,request)
    def test_saved_object_requests_reject_injected_options_or_ambiguous_paths(self):
        base=Path(tempfile.gettempdir()).resolve()
        for mode in stage.OBJECT_STAGES:
            good=self.request(mode,base)
            for bad in (None,[],{},dict(good,extra='--gpu'),dict(good,**{next(iter(good)):'relative'}),dict(good,**{next(iter(good)):True}),dict(good,**{next(iter(good)):'bad\npath'})):
                with self.subTest(mode=mode,bad=bad),self.assertRaises(ValueError):stage.object_request(mode,bad)
        for value in ('A'*64,'a'*63,'g'*64):
            with self.assertRaisesRegex(ValueError,'SHA256'):stage.object_request('jit-link-object',dict(self.request('jit-link-object',base),object_sha256=value))
        with self.assertRaisesRegex(ValueError,'Only saved-object'):stage.recipe('id','gpu','cuda',base/'capture',None,180,{'extra':'value'})
    def test_saved_object_scope_and_outer_failure_cannot_become_battle_success(self):
        for mode in stage.OBJECT_STAGES:
            good=dict(mode=mode+'-only',object_verified=True,containment_verified=True,calculation_verified=False,link_verified=mode=='jit-link-object',kernel_calls=0)
            if mode=='recover-object':good.update(native_tool_calls=0,original_stage_verified=False,original_capture_modified=False,original_outer_timed_out=True)
            variants=[({},True),({},False),({'mode':'gpu'},True),({'object_verified':False},True),({'containment_verified':False},True),({'calculation_verified':True},True),({'kernel_calls':1},True),({'kernel_calls':False},True),({'link_verified':mode!='jit-link-object'},True),({'driver_load_calls':1},True),({'nvrtc_compile_calls':1},True)]
            if mode=='recover-object':variants.extend([(dict(native_tool_calls=1),True),(dict(original_stage_verified=True),True),(dict(original_capture_modified=True),True),(dict(original_outer_timed_out=False),True)])
            for change,outer_passed in variants:
                with tempfile.TemporaryDirectory() as d:
                    base=Path(d);root=base/'packet';root.mkdir();folder=base/'stage';proof=dict(good,**change)
                    def bounded(*args,**kwargs):
                        self.assertEqual(kwargs['env']['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
                        (folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps(proof));return dict(passed=outer_passed)
                    cli=SimpleNamespace(bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
                    with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False):
                        result=stage.run_stage(folder,mode,'cuda',180,base/'original',self.request(mode,base))
                    self.assertEqual(result['diagnostic_verified'],not change)
                    self.assertEqual(result['stage_verified'],not change and outer_passed)
                    self.assertFalse(result['calculation_verified']);self.assertFalse(result['compiler_verified']);self.assertFalse(result['generation_verified'])

    def test_generation_is_separate_cpu_only_preparation(self):
        with patch.dict(stage.os.environ,{'NIKKE_SLANG_GENERATION_CACHE':str(Path('/tmp/generation-cache').resolve())}):
            p=stage.recipe('id','generation','cuda','/tmp/generated-stage','/tmp/original',180)
        self.assertEqual(stage.proof_arguments(p),['generation','--out',p['proof_capture'],'--generation-cache',p['generation_cache'],'--packet-stage',p['capture']])
        self.assertEqual(p['inner_gpu_timeout_seconds'],60);self.assertEqual(p['memory_limit_mb'],2048)
        with patch.dict(stage.os.environ,{'NIKKE_SLANG_GENERATION_CACHE':''}):
            with self.assertRaisesRegex(ValueError,'absolute Slang generation cache'):stage.recipe('id','generation','cuda','/tmp/x','/tmp/original',180)
    def test_generation_receipt_cannot_claim_battle_or_gpu_success(self):
        good=dict(package_id='id',verified=True,sealed_generated_baseline_verified=True,calculation_verified=False,executable_battle_verified=False,gpu_calls=0)
        for change in ({},dict(package_id='other'),dict(gpu_calls=1),dict(gpu_calls=False),dict(calculation_verified=True),dict(executable_battle_verified=True),dict(sealed_generated_baseline_verified=False),dict(mode='compile-only',compiler_verified=True,driver_load_calls=0),dict(driver_load_calls=1),dict(nvrtc_compile_calls=1)):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage';proof=dict(good,**change)
                def bounded(*args,**kw):
                    self.assertEqual(kw['env']['NIKKE_SLANG_GENERATION_REQUIRED'],'0')
                    (folder/'proof').mkdir();(folder/'proof/generation.json').write_text(json.dumps(proof));return dict(passed=True)
                cli=SimpleNamespace(bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
                with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False),patch.dict(stage.os.environ,{'NIKKE_SLANG_GENERATION_CACHE':str(Path(d)/'cache')}):
                    result=stage.run_stage(folder,'generation','cuda',180,'/tmp/original')
                self.assertEqual(result['stage_verified'],not change);self.assertEqual(result['generation_verified'],not change)
                self.assertFalse(result['calculation_verified']);self.assertFalse(result['compiler_verified'])
    def test_recipe_rejects_capture_inside_package_and_original(self):
        with self.assertRaises(ValueError):stage.recipe('id','cpu','cuda',ROOT/'capture',None,180)
        with self.assertRaises(ValueError):stage.recipe('id','cpu','cuda',Path('/tmp/original/capture'),'/tmp/original',180)
    def test_commands_are_fixed_without_shell_or_history_paths(self):
        for mode in ('cpu','gpu','smoke'):
            p=stage.recipe('id',mode,'cuda','/tmp/isolated-stage','/tmp/original',180)
            a=stage.proof_arguments(p);self.assertEqual(a[:3],['run','--backend','cuda']);self.assertIn('--timeout',a);self.assertEqual(a[a.index('--timeout')+1],'60')
            self.assertEqual('--cpu-only' in a,mode=='cpu');self.assertEqual('--smoke' in a,mode=='smoke')
    def test_budget_and_stage_validation(self):
        for timeout in (0,181,True,1.5):
            with self.assertRaises(ValueError):stage.recipe('id','cpu','cuda','/tmp/x',None,timeout)
        with self.assertRaises(ValueError):stage.recipe('id','compile','cuda','/tmp/x',None,180)
        with self.assertRaisesRegex(ValueError,'CUDA backend'):stage.recipe('id','compile-ptx','metal','/tmp/x',None,180)
    def test_compile_stage_is_fixed_ptx_without_run_or_gpu_flags(self):
        p=stage.recipe('id','compile-ptx','cuda','/tmp/isolated-stage','/tmp/original',180)
        args=stage.proof_arguments(p)
        self.assertEqual(args,['compile','--capture',p['proof_capture'],'--timeout','60','--artifact-kind','ptx','--memory-limit-mb','2048','--original-workspace',p['original_workspace']])
        p['original_workspace']=None
        with self.assertRaisesRegex(ValueError,'original workspace'):stage.proof_arguments(p)
    def test_cubin_o0_stage_uses_existing_compiler_and_keeps_the_same_budget(self):
        p=stage.recipe('id','compile-cubin-o0','cuda','/tmp/isolated-stage','/tmp/original',180)
        self.assertEqual(stage.proof_arguments(p),['compile','--capture',p['proof_capture'],'--timeout','60','--artifact-kind','cubin','--memory-limit-mb','2048','--original-workspace',p['original_workspace'],'--ptxas-level','0'])
        with self.assertRaisesRegex(ValueError,'CUDA backend'):stage.recipe('id','compile-cubin-o0','metal','/tmp/x','/tmp/original',180)
        with self.assertRaisesRegex(ValueError,'original workspace'):stage.recipe('id','compile-cubin-o0','cuda','/tmp/x',None,180)
    def test_cubin_o1_preserves_separate_outer_and_inner_budgets(self):
        for outer in (30,60,180):
            p=stage.recipe('id','compile-cubin-o1','cuda','/tmp/isolated-stage','/tmp/original',outer)
            self.assertEqual(p['timeout_seconds'],outer)
            self.assertEqual(p['inner_gpu_timeout_seconds'],min(60,outer))
            self.assertEqual(stage.proof_arguments(p),['compile','--capture',p['proof_capture'],'--timeout',str(min(60,outer)),'--artifact-kind','cubin','--memory-limit-mb','2048','--original-workspace',p['original_workspace'],'--ptxas-level','1'])
        with self.assertRaisesRegex(ValueError,'CUDA backend'):stage.recipe('id','compile-cubin-o1','metal','/tmp/x','/tmp/original',180)
        with self.assertRaisesRegex(ValueError,'original workspace'):stage.recipe('id','compile-cubin-o1','cuda','/tmp/x',None,180)
    def test_compile_result_cannot_promote_driver_or_gpu_work_to_compiler_only_success(self):
        good=dict(mode='compile-only',compiler_verified=True,calculation_verified=False,gpu_calls=0,driver_load_calls=0)
        for mode in stage.COMPILE_STAGES:
          for change in ({},dict(gpu_calls=1),dict(gpu_calls=False),dict(driver_load_calls=1),dict(calculation_verified=True),dict(mode='gpu')):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage';proof=dict(good,**change)
                def bounded(*a,**kw):
                    (folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps(proof));return dict(passed=True)
                cli=SimpleNamespace(bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
                with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False):
                    r=stage.run_stage(folder,mode,'cuda',180,'/tmp/original')
                self.assertEqual(r['compiler_verified'],not change);self.assertEqual(r['stage_verified'],not change)
                self.assertFalse(r['calculation_verified'])
    def test_existing_stage_record_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'claim.json';stage.save(p,{'old':1})
            with self.assertRaises(FileExistsError):stage.save(p,{'new':2})
            self.assertEqual(json.loads(p.read_text()),{'old':1})
    def test_shared_entry_checks_bytes_once_after_gate_and_rejects_mutation(self):
        for corruption in ('none','bytes','identity'):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage';folder.mkdir()
                plan=stage.recipe('id','cpu','metal',folder,Path(d)/'original',90);(folder/'recipe.json').write_text(json.dumps(plan));(folder/'start.json').write_text('{}')
                (root/'member').write_text('tampered' if corruption=='bytes' else 'sealed');calls=[]
                def verify(where):
                    calls.append('verify');self.assertEqual(where,root)
                    if (root/'member').read_text()!='sealed':raise ValueError('Artifact bytes/SHA/size mismatch')
                    return dict(package_id='other' if corruption=='identity' else 'id')
                cli=SimpleNamespace(verify_package=verify,cpu_test_groups=lambda *a:calls.append('cpu'))
                def main():
                    self.assertEqual(sys.argv,[str(root/'scripts/nikke_gpu.py'),*stage.proof_arguments(plan)])
                    cli.cpu_test_groups(cli.verify_package(root),folder)
                cli.main=main
                with patch.object(stage,'ROOT',root),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage.os,'chdir'),patch.object(sys,'argv',list(sys.argv)):
                    if corruption!='none':
                        with self.assertRaisesRegex(ValueError,'Artifact bytes' if corruption=='bytes' else 'Packet changed after stage gate'):stage.child(folder)
                    else:stage.child(folder)
                self.assertEqual(calls,['verify'] if corruption!='none' else ['verify','cpu'])
                events=[json.loads(line) for line in (folder/'preparation.jsonl').read_text().splitlines()]
                self.assertEqual([e['state'] for e in events if e['stage']=='packet_verify_package'],['entered','raised' if corruption!='none' else 'returned'])
                self.assertEqual(events[-1]['stage'],'packet_shared_cli');self.assertEqual(events[-1]['state'],'raised' if corruption!='none' else 'returned')
    def test_missing_containment_gate_never_enters_shared_cli(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage';folder.mkdir()
            plan=stage.recipe('id','cpu','metal',folder,Path(d)/'original',90);(folder/'recipe.json').write_text(json.dumps(plan));main=Mock()
            with patch.object(stage,'ROOT',root),patch.object(stage,'load_module',return_value=SimpleNamespace(main=main)),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage.time,'monotonic',side_effect=[0,31]):
                with self.assertRaisesRegex(RuntimeError,'gate was not released'):stage.child(folder)
            main.assert_not_called();self.assertFalse((folder/'preparation.jsonl').exists())

    def test_missing_or_failed_child_result_never_becomes_success(self):
        # The real bounded owner cleans its process tree; this checks parent
        # interpretation without starting another process or importing a GPU.
        for facts,proof in [({'passed':False},None),({'passed':False},{'cpu_verified':True}),({'passed':True},None),({'passed':True},{'cpu_verified':False})]:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage'
                def bounded(*a,**kw):
                    if proof is not None:(folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps(proof))
                    return facts
                cli=SimpleNamespace(verify_package=lambda _:dict(package_id='id'),bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
                with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False),patch.object(Path,'rglob',side_effect=AssertionError('No historical enumeration')):
                    result=stage.run_stage(folder,'cpu','metal',20)
                self.assertFalse(result['stage_verified']);self.assertEqual(result['cpu_verified'],bool(proof and proof.get('cpu_verified')))
    def test_numeric_proof_is_separate_from_failed_outer_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage'
            def bounded(*args,**kwargs):
                (folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps({'calculation_verified':True,'passed':False,'preservation_verified':False}));return {'passed':False,'child_exit_code':2}
            cli=SimpleNamespace(bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
            with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False):
                result=stage.run_stage(folder,'gpu','metal',20)
            self.assertTrue(result['calculation_verified']);self.assertFalse(result['stage_verified']);self.assertFalse(result['bounded_execution_verified'])
    def test_success_requires_real_proof_receipt_and_owned_completion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage'
            def bounded(command,where,timeout,**kw):
                self.assertEqual(where,folder.resolve());self.assertGreater(timeout,170);self.assertLessEqual(timeout,180);self.assertEqual(command[0],sys.executable);self.assertFalse('shell' in kw);self.assertEqual(kw['env']['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
                (folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps({'cpu_verified':True}));return {'passed':True}
            cli=SimpleNamespace(verify_package=lambda _:dict(package_id='id'),bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
            with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False):
                result=stage.run_stage(folder,'cpu','metal',180)
                self.assertTrue(result['cpu_verified']);self.assertTrue(result['stage_complete'])
                with self.assertRaises(FileExistsError):stage.run_stage(Path(d)/'another','cpu','metal',180)
if __name__=='__main__':unittest.main()
