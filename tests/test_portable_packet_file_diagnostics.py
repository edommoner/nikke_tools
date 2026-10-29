"""Saved statistics/cache checks must use bounded 2GiB stages, never GPU routes."""
import base64,contextlib,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('file_diagnostic_stage',ROOT/'scripts/run-gpu-packet.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)

class FileDiagnosticTests(unittest.TestCase):
    def raw(self,mode):
        common=dict(calculation_verified=False,gpu_calls=0,nvrtc_compile_calls=0)
        if mode=='cache-check':return dict(common,passed=True,package_id='id',cache=dict(enabled=True,hit=True,key='a'*64,artifact_sha256='b'*64,identity=dict(artifact='ptx')))
        return dict(common,compiler_verified=False,receipt_match=True,source_integrity_verified=True,analysis_complete=True,ptx_sha256='a'*64,
                    callgraph=dict(ptx_sha256='a'*64,direct_graph_complete=True,compiler_verified=False,calculation_verified=False))

    def proof(self,mode):
        return dict(mode=mode,package_id='id',detail=self.raw(mode),file_diagnostic_verified=True,compiler_verified=False,calculation_verified=False,gpu_calls=0,compiler_calls=0,native_calls=0)

    def test_recipe_requires_cuda_observer_exact_absolute_paths_and_bounded_budget(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d).resolve()
            for mode,fields in stage.FILE_DIAGNOSTICS.items():
                request={k:str(base/k) for k in fields}
                plan=stage.recipe('id',mode,'cuda',base/'out',base/'original',180,request)
                self.assertEqual(plan['memory_limit_mb'],2048)
                with self.assertRaisesRegex(ValueError,'guarded file-only'):stage.proof_arguments(plan)
                for bad in ({},dict(request,extra='x'),dict(request,**{fields[0]:'relative'}),dict(request,**{fields[0]:str(base)+'\n'})):
                    with self.assertRaises(ValueError):stage.recipe('id',mode,'cuda',base/'out',base/'original',180,bad)
                for backend,original,budget in [('metal',base/'original',180),('cuda',None,180),('cuda',base/'original',181),('cuda',base/'original',True)]:
                    with self.assertRaises(ValueError):stage.recipe('id',mode,backend,base/'out',original,budget,request)

    def test_receipt_cannot_promote_compilation_or_calculation_or_treat_bool_as_zero(self):
        for mode in stage.FILE_DIAGNOSTICS:
            good=self.proof(mode);self.assertTrue(stage.verified_file_diagnostic(good,'id',mode))
            for change in (dict(package_id='wrong'),dict(compiler_verified=True),dict(calculation_verified=True),dict(gpu_calls=False),dict(compiler_calls=1),dict(native_calls=1),dict(detail={})):
                self.assertFalse(stage.verified_file_diagnostic(dict(good,**change),'id',mode))
            for change in (dict(calculation_verified=True),dict(compiler_verified=True),dict(nvrtc_compile_calls=1),dict(gpu_calls=False),dict(driver_load_calls=1),dict(native_battle_calls=1)):
                self.assertFalse(stage.verified_file_diagnostic(dict(good,detail=dict(good['detail'],**change)),'id',mode))
        good=self.proof('cache-check')
        self.assertFalse(stage.verified_file_diagnostic(dict(good,detail=dict(good['detail'],cache=dict(good['detail']['cache'],hit=False))),'id','cache-check'))
        good=self.proof('ptx-stats');raw=good['detail']
        self.assertFalse(stage.verified_file_diagnostic(dict(good,detail=dict(raw,callgraph=dict(raw['callgraph'],ptx_sha256='b'*64))),'id','ptx-stats'))
        # Incomplete call topology is a reported gap, not a fabricated complete graph.
        self.assertTrue(stage.verified_file_diagnostic(dict(good,detail=dict(raw,callgraph=dict(raw['callgraph'],direct_graph_complete=False))),'id','ptx-stats'))

    def test_direct_existing_auditor_delegation_is_gpu_guarded_and_preserves_failure(self):
        for mode,fields in stage.FILE_DIAGNOSTICS.items():
            with tempfile.TemporaryDirectory() as d:
                base=Path(d).resolve();folder=base/'stage';folder.mkdir();request={k:str(base/k) for k in fields}
                plan=stage.recipe('id',mode,'cuda',folder,base/'original',180,request);guard=[]
                @contextlib.contextmanager
                def forbid():
                    guard.append(True)
                    try:yield
                    finally:guard.pop()
                def audit(*args,**kwargs):self.assertTrue(guard);return self.raw(mode)
                cli=SimpleNamespace(forbid_gpu=forbid,verify_package=Mock(return_value=dict(package_id='id')),ptx_statistics=Mock(side_effect=audit),check_compile_cache=Mock(side_effect=audit),collect=Mock())
                stage.run_file_diagnostic(cli,plan)
                method=cli.ptx_statistics if mode=='ptx-stats' else cli.check_compile_cache
                self.assertEqual(method.call_count,1)
                self.assertEqual(cli.verify_package.call_count,int(mode=='ptx-stats'))
                cli.collect.assert_called_once()
                self.assertTrue(stage.verified_file_diagnostic(json.loads((folder/'proof/result.json').read_text()),'id',mode))
                # Exclusive publication is retained; no same-stage replay.
                with self.assertRaises(FileExistsError):stage.run_file_diagnostic(cli,plan)

    def test_actual_saved_ptx_parser_and_graph_run_through_guarded_entry(self):
        import nikke_gpu as cli
        with tempfile.TemporaryDirectory() as d:
            base=Path(d).resolve();ptx=b'.visible .entry kernel() { .reg .b32 %r<2>; ret; }\n'
            identity=dict(artifact='ptx',source_sha256='c'*64);key=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            sha=hashlib.sha256(ptx).hexdigest();entry=base/(key+'.json');phases=base/'phases.jsonl'
            entry.write_text(json.dumps(dict(identity=identity,artifact_base64=base64.b64encode(ptx).decode(),artifact_bytes=len(ptx),artifact_sha256=sha)))
            phases.write_text(json.dumps(dict(stage='cuda_compile_cache',state='verified',receipt=dict(key=key,identity=identity,artifact_sha256=sha,artifact_bytes=len(ptx))))+'\n')
            folder=base/'stage';folder.mkdir();plan=stage.recipe('id','ptx-stats','cuda',folder,base/'original',180,dict(cache_entry=str(entry),phases=str(phases)))
            with patch.object(cli,'verify_package',return_value=dict(package_id='id')):stage.run_file_diagnostic(cli,plan)
            proof=json.loads((folder/'proof/result.json').read_text())
            self.assertEqual(proof['detail']['functions'],1);self.assertEqual(proof['detail']['ptx_sha256'],sha)
            self.assertTrue(stage.verified_file_diagnostic(proof,'id','ptx-stats'))

    def test_failed_audit_retains_partial_evidence_and_never_publishes_success(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d).resolve();folder=base/'stage';folder.mkdir()
            plan=stage.recipe('id','cache-check','cuda',folder,base/'original',180,dict(source_capture=str(base/'saved')))
            def fail(*args):
                (folder/'proof/partial.json').write_text('{"cache_miss":true}')
                raise ValueError('Cache miss; compilation forbidden')
            cli=SimpleNamespace(forbid_gpu=contextlib.nullcontext,check_compile_cache=Mock(side_effect=fail),collect=Mock())
            with self.assertRaisesRegex(ValueError,'compilation forbidden'):stage.run_file_diagnostic(cli,plan)
            self.assertTrue((folder/'proof/partial.json').is_file());self.assertFalse((folder/'proof/result.json').exists())
            cli.collect.assert_called_once()
            with self.assertRaises(FileExistsError):stage.run_file_diagnostic(cli,plan)

    def test_parent_forces_2gib_and_cannot_publish_gpu_or_compiler_success(self):
        for mode in stage.FILE_DIAGNOSTICS:
            with tempfile.TemporaryDirectory() as d:
                base=Path(d).resolve();root=base/'packet';root.mkdir();folder=base/'stage';request={k:str(base/k) for k in stage.FILE_DIAGNOSTICS[mode]}
                def bounded(*args,**kwargs):
                    self.assertEqual(kwargs['env']['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
                    (folder/'proof').mkdir();stage.save(folder/'proof/result.json',self.proof(mode));return dict(passed=True)
                cli=SimpleNamespace(validation_environment=lambda _:dict(NIKKE_VALIDATION_JOB_MEMORY_MB='0'),bounded_module=lambda:SimpleNamespace(run_bounded=bounded))
                with patch.object(stage,'ROOT',root),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'is_windows',return_value=False):
                    result=stage.run_stage(folder,mode,'cuda',180,base/'original',request)
                self.assertTrue(result['file_diagnostic_verified']);self.assertTrue(result['stage_verified'])
                self.assertFalse(result['calculation_verified']);self.assertFalse(result['compiler_verified'])

if __name__=='__main__':unittest.main()
