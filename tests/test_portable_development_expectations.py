"""Expected hashes may cross a GPU edit; native values/checks may never do so."""
import array,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_development_expectations import reuse,validate,digest,ledger_change
s=importlib.util.spec_from_file_location('expectations_test_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)

class ExpectationTests(unittest.TestCase):
    def fixture(self,root):
        old=root/'old';new=root/'new';old.mkdir();new.mkdir()
        names=['app/reference.py','gpu/main.slang','scripts/nikke_gpu.py']
        for p in (old,new):
            for name in names:
                f=p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('// shader\n' if name.endswith('.slang') else '# CPU\n')
        value={'native':123};data=array.array('I',[1,123]).tobytes();sha=lambda v:hashlib.sha256(v).hexdigest()
        fingerprint=lambda v:digest(v)
        golden=dict(input_sha256=sha(data),source_sha256={'gpu/main.slang':sha((old/'gpu/main.slang').read_bytes())},entries=[dict(name='positive',input_sha256=sha(data[4:]),native_sha256=fingerprint(value),output_sha256='f'*64)])
        m=dict(schema=cli.SCHEMA,suite='fixture',purpose='development',selected_cases=[],files=cli.file_records(old,names),golden=golden);m['package_id']=cli.package_id(m);cli.write(old/'gpu-package.json',m)
        calls=[]
        def native(domain):calls.append(domain);return value
        adapter=SimpleNamespace(suite=SimpleNamespace(INPUT=1),prepare=lambda:([('positive',[123],dict(input=123))],data),native_reference=native,cross=SimpleNamespace(digest=fingerprint))
        return old,new,names,adapter,calls
    def context(self,new,adapter):
        import contextlib,portable_backend
        ctx=contextlib.ExitStack();ctx.enter_context(patch.object(cli,'ROOT',new));ctx.enter_context(patch.object(portable_backend,'ROOT',new));ctx.enter_context(patch.dict(cli.SUITES,fixture=dict(source='gpu/main.slang',golden='future.json',tests=[])));ctx.enter_context(patch.object(cli,'open_suite',return_value=adapter));return ctx
    def test_gpu_edit_keeps_only_expected_hashes_and_preflight_recalculates(self):
        with tempfile.TemporaryDirectory() as folder:
            old,new,names,adapter,calls=self.fixture(Path(folder));(new/'gpu/main.slang').write_text('// changed GPU\n')
            with self.context(new,adapter),cli.forbid_gpu():
                records=cli.file_records(new,names);g,r=reuse(cli,'fixture',old,records,[])
                self.assertEqual(calls,[]);self.assertNotIn('output_sha256',g);self.assertNotIn('output_sha256',g['entries'][0]);self.assertEqual(r['changed_gpu_sources'],['gpu/main.slang'])
                m=dict(suite='fixture',purpose='development',files=records,golden=g,native_expectation_baseline=r)
                self.assertTrue(validate(m));result=cli.cpu_preflight(m)
                self.assertEqual(len(calls),1);self.assertEqual(result['native_oracles'],1)
                adapter.native_reference=lambda _:dict(native=999)
                with self.assertRaisesRegex(ValueError,'First CPU/input mismatch'):cli.cpu_preflight(m)
    def test_cpu_data_membership_and_selection_changes_fail_before_native(self):
        for variant in ('cpu','missing','added','selection','input','fingerprint','corrupt-baseline'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as folder:
                old,new,names,adapter,calls=self.fixture(Path(folder));cases=[]
                if variant=='cpu':(new/'app/reference.py').write_text('# changed CPU\n')
                if variant=='missing':names.remove('app/reference.py')
                if variant=='added':names.append('app/extra.py');(new/'app/extra.py').write_text('# extra\n')
                if variant=='selection':cases=['positive']
                if variant=='input':adapter.prepare=lambda:([('positive',[124],{})],array.array('I',[1,124]).tobytes())
                if variant in ('fingerprint','corrupt-baseline'):
                    m=cli.load(old/'gpu-package.json')
                    if variant=='fingerprint':m['golden']['entries'][0]['native_sha256']='missing'
                    else:m['golden']['input_sha256']='0'*64
                    m['package_id']=cli.package_id(m);cli.write(old/'gpu-package.json',m)
                with self.context(new,adapter),cli.forbid_gpu(),self.assertRaises(ValueError):reuse(cli,'fixture',old,cli.file_records(new,names),cases)
                self.assertEqual(calls,[])
    def test_receipt_cannot_skip_checks_claim_success_or_carry_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            old,new,names,adapter,_=self.fixture(Path(folder))
            with self.context(new,adapter):
                records=cli.file_records(new,names);g,r=reuse(cli,'fixture',old,records,[])
            m=dict(purpose='development',files=records,golden=g,native_expectation_baseline=r)
            for key,value in [('fresh_native_preflight_required',False),('independent_seal_required',False),('calculation_verified',True),('gpu_calls',1),('native_battles_recomputed_during_package',1),('candidate_files_sha256','0'*64),('fingerprints_sha256','0'*64),('source_sha256','0'*64),('retained_cases',0),('runtime_oracles',[123]),('changed_gpu_sources',['gpu/../secret.slang'])]:
                bad=copy.deepcopy(m);bad['native_expectation_baseline'][key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):validate(bad)
            bad=copy.deepcopy(m);bad['purpose']='sealed'
            with self.assertRaises(ValueError):validate(bad)
            bad=copy.deepcopy(m);bad['golden']['entries'][0]['output_sha256']='f'*64
            with self.assertRaises(ValueError):validate(bad)
    def test_slang_ledger_allows_current_gpu_edits_but_never_baseline_or_cpu_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);old=root/'old';new=root/'new';name='tests/fixtures/shared-source-delta.json'
            for p,current in ((old,'old GPU'),(new,'new GPU')):
                (p/'gpu').mkdir(parents=True);(p/'gpu/main.slang').write_text(current)
                baseline='frozen baseline';row={k:v for k,v in [('baseline',baseline),('baseline_sha256',hashlib.sha256(baseline.encode()).hexdigest()),('current',current),('current_sha256',hashlib.sha256(current.encode()).hexdigest())]}
                f=p/name;f.parent.mkdir(parents=True);f.write_text(json.dumps(dict(sources={'gpu/main.slang':row},added_sources={})))
            self.assertTrue(ledger_change(old,new,name))
            raw=(new/name).read_text();d=json.loads(raw);d['sources']['gpu/main.slang']['baseline']='different';(new/name).write_text(json.dumps(d));self.assertFalse(ledger_change(old,new,name))
            (new/name).write_text(raw);(new/'gpu/main.slang').write_text('unreviewed');self.assertFalse(ledger_change(old,new,name))
            self.assertFalse(ledger_change(old,new,'tests/fixtures/../../secret-source-delta.json'))
    def test_added_gpu_hash_ledger_is_checked_and_cpu_ledger_changes_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            old,new,names,adapter,_=self.fixture(Path(folder));name='tests/fixtures/typed-source-delta.json';names.append(name)
            (new/'gpu/main.slang').write_text('// GPU edit\n')
            for root in (old,new):
                f=root/name;f.parent.mkdir(parents=True);f.write_text(json.dumps(dict(sources={},added_sources={'gpu/main.slang':cli.sha((root/'gpu/main.slang').read_bytes()),'app/reference.py':cli.sha((root/'app/reference.py').read_bytes())})))
            m=cli.load(old/'gpu-package.json');m['files']=cli.file_records(old,names);m['package_id']=cli.package_id(m);cli.write(old/'gpu-package.json',m)
            with self.context(new,adapter):
                _,r=reuse(cli,'fixture',old,cli.file_records(new,names),[]);self.assertEqual(r['verified_slang_ledgers'],[name])
                d=json.loads((new/name).read_text());d['added_sources']['app/reference.py']='0'*64;(new/name).write_text(json.dumps(d))
                with self.assertRaisesRegex(ValueError,'Native baseline dependency differs'):reuse(cli,'fixture',old,cli.file_records(new,names),[])
    def test_sealed_baseline_supplies_expectations_without_transferring_its_gpu_proof(self):
        with tempfile.TemporaryDirectory() as folder:
            old,new,names,adapter,_=self.fixture(Path(folder));m=cli.load(old/'gpu-package.json');m['purpose']='sealed'
            for root in (old,new):(root/'future.json').write_text(json.dumps(m['golden']))
            names.append('future.json');m['files']=cli.file_records(old,names);m['package_id']=cli.package_id(m);cli.write(old/'gpu-package.json',m)
            with self.context(new,adapter):
                g,r=reuse(cli,'fixture',old,cli.file_records(new,names),[])
                self.assertNotIn('output_sha256',g['entries'][0]);self.assertFalse(r['calculation_verified']);self.assertTrue(r['independent_seal_required'])
                m['baseline_migration']={'unknown':True};m['package_id']=cli.package_id(m);cli.write(old/'gpu-package.json',m)
                with self.assertRaisesRegex(ValueError,'Observation migration'):reuse(cli,'fixture',old,cli.file_records(new,names),[])
    def test_option_requires_development_and_cannot_launder_migration_packages(self):
        for options in (dict(),dict(develop=True,baseline_package=Path('/unused')),dict(develop=True,reference_migration='coordinate-healing-routed-adds-v1')):
            with self.subTest(options=options),patch.dict(cli.SUITES,fixture=dict()),patch.object(cli.subprocess,'check_output',side_effect=AssertionError('Must fail before source discovery')):
                with self.assertRaisesRegex(ValueError,'Native expectations require'):cli.make_package('fixture',Path('/unused.zip'),native_baseline_package=Path('/unused'),**options)
    def test_unicode_ledger_ignores_non_utf8_host_default(self):
        with tempfile.TemporaryDirectory() as folder:
            roots=[Path(folder)/p for p in ('old','new')];name='tests/fixtures/unicode-source-delta.json'
            for root,current in zip(roots,('// 座標 좌표 old','// 座標 좌표 new'),strict=True):
                (root/'gpu').mkdir(parents=True);(root/'gpu/main.slang').write_text(current,encoding='utf-8')
                baseline='// 共通 기준';row=dict(baseline=baseline,baseline_sha256=cli.sha(baseline.encode()),current=current,current_sha256=cli.sha(current.encode()))
                f=root/name;f.parent.mkdir(parents=True);f.write_text(json.dumps(dict(sources={'gpu/main.slang':row},added_sources={}),ensure_ascii=False),encoding='utf-8')
            original=Path.open
            def cp932_default(path,*args,**kwargs):
                mode=args[0] if args else kwargs.get('mode','r')
                if 'b' not in mode and kwargs.get('encoding') in (None,'locale'):kwargs['encoding']='cp932'
                return original(path,*args,**kwargs)
            with patch.object(Path,'open',cp932_default):self.assertTrue(ledger_change(*roots,name))
if __name__=='__main__':unittest.main()
