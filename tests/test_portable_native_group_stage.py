"""Bounded CUDA native groups retain the shared auditor and partial scope."""
import copy,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import test_portable_comparison_groups as groups
s=importlib.util.spec_from_file_location('native_group_packet',ROOT/'scripts/run-gpu-packet.py');stage=importlib.util.module_from_spec(s);s.loader.exec_module(stage)
cli=groups.cli


class NativeGroupStageTests(unittest.TestCase):
    def test_pinned_explicit_plan_flows_to_the_same_bounded_stage(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'plan.json';p.write_bytes(b'[[0],[1,2]]')
            request=dict(self.request(root),case_groups=str(p),case_groups_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            plan=stage.recipe('controller','audit-native-group','cuda',root/'out',root/'original',180,request)
            args=stage.proof_arguments(plan);self.assertEqual(args[args.index('--case-groups')+1],str(p))
            proof=self.proof(root);proof['planned']=[[0],[1,2]]
            self.assertFalse(stage.verified_native_group(proof,request))
            comparison=proof['group']['comparison'];comparison['case_indices']=[0];comparison['entries']=comparison['entries'][:1]
            comparison['input_count']=1;comparison['native_oracles']=1
            self.assertTrue(stage.verified_native_group(proof,request))
            p.write_bytes(b'[[0,1],[2]]')
            self.assertFalse(stage.verified_native_group(proof,request))
            for key in ('case_groups','case_groups_sha256'):
                with self.assertRaises(ValueError):stage.object_request('audit-native-group',{k:v for k,v in request.items() if k!=key})
    def request(self,root,index=0):
        return dict(source_package=str(root/'source'),source_capture=str(root/'saved'),group_index=str(index),group_size='2')
    def proof(self,root,index=0):
        request=self.request(root,index);m,rows,planned=groups.CoverageTests().fixture();g=rows[index]
        g['audit'].update(transport_core_verified=True,containment_verified=True,preservation_verified=True,comparison_error=None)
        return dict(mode='saved-native-group-only',backend='cuda',package_id=m['package_id'],group_index=index,group_size=2,planned=planned,
            source_package=request['source_package'],source_capture=request['source_capture'],per_group_timeout_seconds=180,
            comparison_subset_verified=True,calculation_verified=False,gpu_calls=0,group=g)
    def test_request_and_forwarding_have_no_gpu_compile_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();request=self.request(root)
            p=stage.recipe('controller','audit-native-group','cuda',root/'out',root/'original',180,request)
            args=stage.proof_arguments(p)
            self.assertEqual(args,['saved-battle-audit','--backend','cuda','--package-root',request['source_package'],'--capture',request['source_capture'],'--group-index','0','--group-size','2','--timeout','180','--out',str(root/'out/proof/result.json')])
            self.assertEqual(p['memory_limit_mb'],2048)
            for key,value in (('group_index','-1'),('group_index','01'),('group_size','0'),('group_size','1.5'),('group_size','١'),('group_index',True)):
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):stage.object_request('audit-native-group',dict(request,**{key:value}))
    def test_partial_proof_cannot_become_whole_calculation_or_change_source(self):
        root=Path('/fixture');proof=self.proof(root);request=self.request(root)
        self.assertTrue(stage.verified_native_group(proof,request))
        changes=[dict(calculation_verified=True),dict(group_index=False),dict(gpu_calls=False),dict(group_index=1),dict(source_capture='/other'),dict(planned=[[0,1]]),dict(per_group_timeout_seconds=181)]
        for change in changes:self.assertFalse(stage.verified_native_group(dict(proof,**change),request))
        for mutate in (lambda x:x['group'].update(live_parent_receipt_present=True),lambda x:x['group']['comparison'].update(case_indices=[1,2]),lambda x:x['group']['audit'].update(containment_verified=False),lambda x:x.update(planned=[[False,1],[2]]),lambda x:x['group']['comparison'].update(case_indices=[False,1])):
            bad=copy.deepcopy(proof);mutate(bad);self.assertFalse(stage.verified_native_group(bad,request))
    def test_claims_allow_distinct_groups_and_reject_same_group_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();packet=root/'controller';packet.mkdir();calls=[]
            def bounded(*args,**kwargs):
                folder=Path(args[1]);index=int(json.loads((folder/'recipe.json').read_text())['object_request']['group_index']);calls.append(index)
                (folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps(self.proof(root,index)))
                self.assertEqual(kwargs['env']['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048');return dict(passed=True)
            c=SimpleNamespace(bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
            with patch.object(stage,'ROOT',packet),patch.object(stage,'packet_header',return_value=dict(package_id='controller')),patch.object(stage,'load_module',return_value=c),patch.object(stage,'is_windows',return_value=False):
                for index in (0,1):
                    r=stage.run_stage(root/('group'+str(index)),'audit-native-group','cuda',180,root/'original',self.request(root,index))
                    self.assertTrue(r['stage_verified']);self.assertFalse(r['calculation_verified'])
                with self.assertRaises(FileExistsError):stage.run_stage(root/'replay','audit-native-group','cuda',180,root/'original',self.request(root,0))
            self.assertEqual(calls,[0,1])
    def test_cuda_fresh_child_keeps_unidentified_service_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root,other,capture=groups.FreshProcessTests().fixture(base)
            cli.write(capture/'run.json',dict(backend='cuda'));cli.write(capture/'execution.json',dict(passed=True))
            m=cli.load(root/'gpu-package.json');m['purpose']='sealed';cli.write(root/'gpu-package.json',m)
            path=root/'scripts/nikke_gpu.py';code=path.read_text().replace('def is_development(m):return True','def is_development(m):return False')
            code=code.replace("return dict(transport_verified=True,calculation_verified=r['calculation_verified'],passed=False)","return dict(transport_verified=False,containment_verified=True,preservation_verified=False,comparison_error=None,phase=dict(nvrtc_compile_returned_success=False,cuda_compile_cache_hit_verified=True,cuda_linked_artifact_observed=False,cuda_launch_returned_success=True,cuda_synchronize_returned_success=True,cuda_readback_returned_success=True),calculation_verified=r['calculation_verified'],passed=False)")
            path.write_text(code)
            receipts=[]
            with patch.object(cli,'ROOT',other):
                for index in (0,1):
                    row=cli.audit_saved_battle_groups(root,capture,backend='cuda',timeout=30,group_size=2,group_index=index)
                    p=base/('receipt'+str(index)+'.json');cli.write(p,row);receipts.append(p)
                    self.addCleanup(lambda path=row['group_capture']:__import__('shutil').rmtree(path))
                final=cli.aggregate_saved_native_groups(root,receipts,'cuda',2,30)
                self.assertTrue(final['audit']['calculation_verified']);self.assertFalse(final['audit']['passed'])
                self.assertEqual(final['comparison']['input_count'],3)
                with self.assertRaises(ValueError):cli.aggregate_saved_native_groups(root,receipts[:1],'cuda',2,30)
                with self.assertRaises(ValueError):cli.aggregate_saved_native_groups(root,receipts[::-1],'cuda',2,30)
                broken=cli.load(receipts[1]);broken['audit_anchors']['capture_files'][0]['sha256']='changed';cli.write(receipts[1],broken)
                with self.assertRaisesRegex(ValueError,'different original evidence'):cli.aggregate_saved_native_groups(root,receipts,'cuda',2,30)
            r=cli.load(receipts[0])
            self.assertTrue(r['comparison_subset_verified']);self.assertFalse(r['calculation_verified'])
            self.assertTrue(r['group']['audit']['transport_core_verified']);self.assertFalse(r['group']['audit']['transport_verified'])
            self.assertFalse(r['group']['audit']['preservation_verified']);self.assertNotEqual(r['group']['child_pid'],os.getpid())


if __name__=='__main__':unittest.main()
