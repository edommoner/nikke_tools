"""Full comparison coverage and partial-result proof boundaries, with real bytes."""
import array,copy,hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_comparison_groups import selection,partition,aggregate,validate_facts
s=importlib.util.spec_from_file_location('group_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
H=lambda raw:hashlib.sha256(raw).hexdigest()

class CoverageTests(unittest.TestCase):
    def fixture(self):
        entries=[dict(name=str(i),input_sha256='in'+str(i),native_sha256='native'+str(i)) for i in range(3)]
        m=dict(package_id='immutable',golden=dict(entries=entries,input_sha256='allinput'))
        groups=[]
        for indices,pid in [([0,1],os.getpid()+10000),([2],os.getpid()+10001)]:
            rows=[dict(entries[i],output_sha256='out'+str(i)) for i in indices]
            c=dict(case_indices=indices,total_input_count=3,input_count=len(indices),entries=rows,comparison_subset_verified=True,calculation_verified=False,mismatches=[],audit_gpu_calls=0,native_oracles=len(indices),input_sha256='allinput',output_sha256='alloutput',generated_normalized={'cuda':'cu','metal':'msl'})
            groups.append(dict(package_id='immutable',comparison=c,audit=dict(transport_verified=True,calculation_verified=False,passed=False),child_pid=pid,elapsed_seconds=.1,live_parent_receipt_present=False))
        return m,groups,[[0,1],[2]]
    def test_all_inputs_once_including_last_short_group(self):
        m,g,p=self.fixture();self.assertEqual(partition(3,2),p);r=aggregate(m,g,p,180)
        self.assertTrue(r['comparison']['calculation_verified']);self.assertEqual(len(r['comparison']['entries']),3);self.assertTrue(r['audit']['passed']);validate_facts(r['independent_comparison'],3,180)
    def test_cuda_calculation_does_not_promote_unknown_service_or_weaken_metal(self):
        m,g,p=self.fixture()
        for row in g:row['audit'].update(transport_verified=False,transport_core_verified=True,containment_verified=True,preservation_verified=False)
        r=aggregate(m,g,p,180,backend='cuda')
        self.assertTrue(r['audit']['calculation_verified']);self.assertFalse(r['audit']['passed'])
        self.assertFalse(r['audit']['transport_verified']);self.assertFalse(r['audit']['preservation_verified'])
        validate_facts(r['independent_comparison'],3,180,backend='cuda')
        with self.assertRaises(ValueError):validate_facts(r['independent_comparison'],3,180)
        with self.assertRaises(ValueError):aggregate(m,g,p,180)
        for key,value in (('transport_core_verified',False),('containment_verified',False),('preservation_verified',None),('transport_verified',True)):
            bad=copy.deepcopy(g);bad[0]['audit'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):aggregate(m,bad,p,180,backend='cuda')
    def test_no_missing_overlapping_reordered_duplicate_or_boolean_indices(self):
        m,g,_=self.fixture()
        for p in ([[0,1]],[[0,1],[1,2]],[[1,0],[2]],[[0,0],[1,2]],[[False,1],[2]]):
            with self.subTest(p=p),self.assertRaises(ValueError):aggregate(m,g,p,180)
        for v in ([],[True],[2,1],[-1],[3]):
            with self.assertRaises(ValueError):selection(3,v)
        for size in (0,-1,True,1.5):
            with self.assertRaises(ValueError):partition(3,size)
    def test_stale_reused_partial_failed_or_unbounded_child_never_certifies(self):
        mutations=[lambda x:x.update(package_id='other'),lambda x:x.update(child_pid=os.getpid()),lambda x:x.update(live_parent_receipt_present=True),lambda x:x.update(elapsed_seconds=182),lambda x:x['comparison'].update(calculation_verified=True),lambda x:x['comparison'].update(parent_oracles={}),lambda x:x['comparison'].update(comparison_subset_verified=False),lambda x:x['comparison'].update(input_count=True),lambda x:x['comparison'].update(input_sha256='stale'),lambda x:x['audit'].update(transport_verified=False),lambda x:x['comparison']['entries'][0].update(native_sha256='changed'),lambda x:x['comparison'].update(native_oracles=True),lambda x:x['comparison'].update(case_indices=[False,1])]
        for mutate in mutations:
            m,g,p=self.fixture();mutate(g[0])
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):aggregate(m,g,p,180)
    def test_shared_raw_generation_and_transport_must_agree(self):
        for key in ('output_sha256','generated_normalized'):
            m,g,p=self.fixture();g[1]['comparison'][key]='changed'
            with self.assertRaises(ValueError):aggregate(m,g,p,180)
        m,g,p=self.fixture();g[1]['audit']['phase']='changed'
        with self.assertRaises(ValueError):aggregate(m,g,p,180)
    def test_receipt_cannot_drop_reject_or_change_counts_or_bound(self):
        m,g,p=self.fixture();r=aggregate(m,g,p,180)['independent_comparison']
        for mutate in (lambda x:x['groups'][1].update(case_indices=[1]),lambda x:x.update(native_cases=2),lambda x:x['groups'][0].update(elapsed_seconds=182),lambda x:x.update(live_parent_receipt_present=True),lambda x:x['groups'][0].update(input_count=True)):
            bad=copy.deepcopy(r);mutate(bad)
            with self.assertRaises(ValueError):validate_facts(bad,3,180)

class GroupedSealTests(unittest.TestCase):
    def test_grouped_receipt_bounds_each_child_and_reports_total_elapsed(self):
        m,g,p=CoverageTests().fixture();r=aggregate(m,g,p,180)
        proof=dict(r,package_id=m['package_id'],golden=dict(entries=r['comparison']['entries'],input_sha256='input',output_sha256='output',source_sha256={}),independent_audit_seconds=220)
        with tempfile.TemporaryDirectory() as tmp,patch.object(cli,'audit_saved_metal',return_value=proof) as audit:
            root=Path(tmp);result=cli.seal_development(root,root/'capture',root/'golden.json',timeout=180,audit_receipt=root/'receipt.json',comparison_group_size=2)
            self.assertTrue(result['sealed']);saved=cli.load(root/'receipt.json');self.assertEqual(saved['schema'],'independent-metal-audit-groups-v1');self.assertEqual(saved['elapsed_seconds'],220);self.assertEqual(saved['per_group_timeout_seconds'],180);self.assertEqual(len(saved['groups']),2);audit.assert_called_once()


class ActualComparatorTests(unittest.TestCase):
    def test_partial_actual_bytes_compute_only_selected_native_and_never_full_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=root/'capture';capture.mkdir()
            data=b'full-input';raw=array.array('I',[0,123,64,0]).tobytes();(capture/'input.bin').write_bytes(data);(capture/'readback.bin').write_bytes(raw)
            for name in ('generated.cu','generated.metal'):(capture/name).write_bytes(b'generated')
            cli.write(capture/'evidence.json',dict(output_sha256=H(raw),input_sha256=H(data),source_sha256={},gpu_execution_verified=True,backend='metal'))
            entries=[('native',[0],object()),('reject',[0],None)];digest=lambda value:H(json.dumps(value,sort_keys=True).encode())
            expected=[dict(name='native',input_sha256=H(data[4:8]),native_sha256=digest({'answer':123})),dict(name='reject',input_sha256=H(data[8:12]),native_sha256=digest({'status':64}))]
            m=dict(suite='fixture',purpose='development',golden=dict(input_sha256=H(data),source_sha256={},entries=expected));calls=[];rejects=[]
            def compare(block,domain):calls.append(domain);return dict(answer=block[1])
            a=SimpleNamespace(suite=SimpleNamespace(INPUT=1),compare=compare,validate_rejection=lambda block,name:rejects.append(name),cross=SimpleNamespace(digest=digest,normalized=lambda b:H(b)))
            with patch.object(cli,'ROOT',root),patch.object(cli,'SUITES',{'fixture':{'output_words':2}}),patch.object(cli,'prepare_entries',return_value=(entries,data)),patch.object(cli,'audit_generation_capture'):
                first=cli.compare_readback(m,capture,a,case_indices=[0]);self.assertEqual(len(calls),1);self.assertEqual(rejects,[]);self.assertFalse(first['calculation_verified']);self.assertTrue(first['comparison_subset_verified'])
                second=cli.compare_readback(m,capture,a,case_indices=[1]);self.assertEqual(len(calls),1);self.assertEqual(rejects,['reject']);self.assertFalse(second['calculation_verified'])
                full=cli.compare_readback(m,capture,a);self.assertTrue(full['calculation_verified']);self.assertNotIn('case_indices',full)
    def test_group_rejects_live_parent_before_io(self):
        with self.assertRaisesRegex(ValueError,'live-parent'):cli.compare_readback({},Path('unused'),parent_oracles=object(),case_indices=[0])
    def test_group_wrapper_does_not_promote_partial_to_capture_success(self):
        calls=[]
        def compare(*args,**kwargs):calls.append(kwargs);return dict(comparison_subset_verified=True,calculation_verified=False)
        m=SimpleNamespace(compare_readback=compare,forbid_gpu=cli.contextlib.nullcontext)
        def audit(capture):m.compare_readback({},capture);return dict(transport_verified=True,calculation_verified=False,passed=False)
        m.audit_capture=audit;a,c=cli.audited_comparison_group(m,'capture',[0]);self.assertFalse(a['passed']);self.assertFalse(c['calculation_verified']);self.assertEqual(calls,[dict(case_indices=[0])]);self.assertIs(m.compare_readback,compare)


class FreshProcessTests(unittest.TestCase):
    def fixture(self,base):
        root=base/'package';other=base/'other';capture=base/'capture'
        for folder in (root,other):(folder/'gpu').mkdir(parents=True);(folder/'gpu/proof.slang').write_text('same source')
        (root/'scripts').mkdir();(root/'research').mkdir();capture.mkdir()
        (root/'research/oracle.py').write_text("VALUE='immutable-package'\n")
        m=dict(package_id='frozen',purpose='development',golden=dict(input_sha256='input',source_sha256={'gpu/proof.slang':H(b'same source')},entries=[dict(name=str(i),input_sha256=str(i),native_sha256='immutable-package') for i in range(3)]))
        cli.write(root/'gpu-package.json',m);cli.write(capture/'artifacts.json',{'files':[]});cli.write(capture/'run.json',{'backend':'metal'})
        for n in ('input.bin','readback.bin','generated.cu','generated.metal'):(capture/n).write_bytes(b'bytes')
        code='''import contextlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_bytes())
def verify_package(root):return load(root/'gpu-package.json')
def is_development(m):return True
forbid_gpu=contextlib.nullcontext
def compare_readback(m,capture,*,case_indices):
    label=runpy.run_path('research/oracle.py')['VALUE']
    entries=[dict(m['golden']['entries'][i],native_sha256=label,output_sha256=str(i)) for i in case_indices]
    return dict(entries=entries,case_indices=case_indices,total_input_count=3,input_count=len(entries),native_oracles=len(entries),input_sha256='input',output_sha256='output',generated_normalized={},comparison_subset_verified=True,calculation_verified=False,mismatches=[],audit_gpu_calls=0)
def audit_capture(capture):
    r=compare_readback(verify_package(ROOT),capture)
    return dict(transport_verified=True,calculation_verified=r['calculation_verified'],passed=False)
'''
        (root/'scripts/nikke_gpu.py').write_text(code)
        return root,other,capture
    def test_real_fresh_children_import_only_immutable_package_and_preserve_all_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root,other,capture=self.fixture(base)
            with patch.object(cli,'ROOT',other):r=cli.audit_saved_metal_groups(root,capture,timeout=30,development_only=True,group_size=2)
            self.assertTrue(r['audit']['calculation_verified']);self.assertEqual(r['comparison']['native_oracles'],3);self.assertEqual(len(set(r['independent_comparison']['child_pids'])),2)
            logs=Path(r['group_capture']);self.addCleanup(lambda:__import__('shutil').rmtree(logs));self.assertTrue((logs/'0.stdout.log').is_file());self.assertTrue((logs/'1.json').is_file());self.assertTrue((logs/'aggregate.json').is_file())
    def test_single_group_is_fresh_and_cannot_claim_full_calculation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root,other,capture=self.fixture(base)
            with patch.object(cli,'ROOT',other):r=cli.audit_saved_battle_groups(root,capture,timeout=30,group_size=2,group_index=1,backend='metal')
            self.assertFalse(r['calculation_verified']);self.assertTrue(r['comparison_subset_verified'])
            self.assertEqual(r['group']['comparison']['case_indices'],[2]);self.assertEqual(r['planned'],[[0,1],[2]])
            self.assertNotEqual(r['group']['child_pid'],os.getpid());self.assertFalse(r['group']['live_parent_receipt_present'])
            logs=Path(r['group_capture']);self.addCleanup(lambda:__import__('shutil').rmtree(logs))
            self.assertFalse((logs/'0.json').exists());self.assertTrue((logs/'1.json').exists());self.assertFalse((logs/'aggregate.json').exists())
    def test_failed_child_stops_later_groups_and_keeps_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root,other,capture=self.fixture(base)
            p=root/'scripts/nikke_gpu.py';p.write_text(p.read_text().replace("label=runpy.run_path('research/oracle.py')['VALUE']","raise ValueError('injected-native-failure')"))
            with patch.object(cli,'ROOT',other),self.assertRaisesRegex(RuntimeError,'preserved logs:') as error:cli.audit_saved_metal_groups(root,capture,timeout=30,development_only=True,group_size=2)
            logs=Path(str(error.exception).split('preserved logs: ',1)[1]);self.addCleanup(lambda:__import__('shutil').rmtree(logs));self.assertIn('injected-native-failure',(logs/'0.stderr.log').read_text());self.assertEqual(cli.load(logs/'failure.json')['completed_groups'],0);self.assertFalse((logs/'1.json').exists());self.assertFalse((logs/'aggregate.json').exists())
    def test_timeout_keeps_partial_logs_and_stops_before_any_success(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root,other,capture=self.fixture(base)
            manifest=cli.load(root/'gpu-package.json')
            with patch.object(cli,'verify_saved_package',return_value=manifest),patch.object(cli.subprocess,'run',side_effect=subprocess.TimeoutExpired(['group'],1,output=b'partial-out',stderr=b'partial-err')),self.assertRaisesRegex(RuntimeError,'preserved logs:') as error:
                cli.audit_saved_metal_groups(root,capture,timeout=1,development_only=True,group_size=2)
            logs=Path(str(error.exception).split('preserved logs: ',1)[1]);self.addCleanup(lambda:__import__('shutil').rmtree(logs));self.assertEqual((logs/'0.stdout.log').read_text(),'partial-out');self.assertEqual((logs/'0.stderr.log').read_text(),'partial-err');self.assertFalse((logs/'aggregate.json').exists())

if __name__=='__main__':unittest.main()
