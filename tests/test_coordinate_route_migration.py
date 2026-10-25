"""The passive ADD-label correction cannot change other native evidence."""
import array,copy,importlib.util,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_coordinate_route_migration import NAME,CASE,SOURCES,digest,verify
class MigrationTests(unittest.TestCase):
    def setUp(self):
        labels=['__enemy__','front','__enemy__:healing-adds#1','__enemy__:healing-adds#2']
        self.ref=dict(battle=dict(damage=[34000]),landed_packets=[dict(label=n,target='' if n=='__enemy__' else n,generation=1,damage=2000,owner=0,time=0.) for n in labels])
        prior=copy.deepcopy(self.ref)
        for r in prior['landed_packets']:
            r.pop('label')
            if r['target'].startswith('__enemy__:healing-adds#'):r['target']=''
        self.old=dict(suite='coordinate-healing',files=[dict(path=p,sha256=h[0]) for p,h in SOURCES.items()],golden=dict(input_sha256='fixed',source_sha256={'gpu/x':'fixed'},entries=[dict(name=CASE,input_sha256='fixed',native_sha256=digest(prior)),dict(name='retained',input_sha256='fixed',native_sha256='fixed')]))
        self.new=copy.deepcopy(self.old)
        for row in self.new['files']:row['sha256']=SOURCES[row['path']][1]
        self.new['golden']['entries'][0]['native_sha256']=digest(self.ref)
    def test_only_actual_recipient_labels_change(self):
        r=verify(NAME,self.old,self.new,self.ref);self.assertTrue(r['all_other_native_fields_equal']);self.assertEqual(r['corrected_packets'],2)
    def test_other_native_amount_owner_clock_or_generation_changes_reject(self):
        for key in ['damage','owner','time','generation']:
            n=copy.deepcopy(self.ref);n['landed_packets'][0][key]+=1;m=copy.deepcopy(self.new);m['golden']['entries'][0]['native_sha256']=digest(n)
            with self.subTest(key=key),self.assertRaises(ValueError):verify(NAME,self.old,m,n)
    def test_other_input_source_observer_or_case_changes_reject(self):
        for key in ['input','source','observer','other','unknown']:
            n=copy.deepcopy(self.new)
            if key=='input':n['golden']['input_sha256']='different'
            if key=='source':n['golden']['source_sha256']['gpu/x']='different'
            if key=='observer':n['files'][0]['sha256']='different'
            if key=='other':n['golden']['entries'][1]['native_sha256']='different'
            with self.subTest(key=key),self.assertRaises(ValueError):verify('unknown' if key=='unknown' else NAME,self.old,n,self.ref)
    def test_missing_or_inconsistent_actual_targets_reject(self):
        for key in ['label','target']:
            n=copy.deepcopy(self.ref);n['landed_packets'][2][key]='body'
            with self.subTest(key=key),self.assertRaises(ValueError):verify(NAME,self.old,self.new,n)
    def cli(self):
        s=importlib.util.spec_from_file_location('route_baseline_test',Path(__file__).resolve().parents[1]/'scripts/nikke_gpu.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    def setup_baseline(self,api):
        self.old.update(purpose='development',selected_cases=[])
        paths=['gpu/x','app/portable_backend.py','app/portable_compile_cache.py','scripts/run-metal-probe.swift','app/portable_generation_cache.py','app/portable_slang_generation.py','app/portable_metal_cache.py','research/summarize-portable-cross-gpu.py','app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py']
        for p in paths:self.old['files'].append(dict(path=p,sha256='fixed'));self.new['files'].append(dict(path=p,sha256='fixed'))
        entries=[(CASE,[1,2],('domain',)),('retained',[3,4],None)];data=array.array('I',[2,1,2,3,4]).tobytes()
        self.old['golden']['input_sha256']=api.sha(data)
        for i,row in enumerate(self.old['golden']['entries']):row['input_sha256']=api.sha(data[4+i*8:12+i*8])
        self.old['package_id']='source'
        return entries,data
    def test_baseline_migration_prepares_all_inputs_but_recomputes_only_changed_observation(self):
        api=self.cli();entries,data=self.setup_baseline(api);calls=[]
        def native(domain):calls.append(domain);return self.ref
        adapter=SimpleNamespace(prepare=lambda:(entries,data),suite=SimpleNamespace(INPUT=2),cross=SimpleNamespace(digest=digest),native_reference=native)
        with patch.object(api,'verify_saved_package',return_value=self.old),patch.object(api,'open_suite',return_value=adapter):g,r=api.migrated_development_baseline('coordinate-healing',Path('/source'),self.new['files'],NAME)
        self.assertEqual(calls,[('domain',)]);self.assertEqual(g['entries'][1],self.old['golden']['entries'][1]);self.assertTrue(r['full_fresh_saved_replay_required']);self.assertFalse(r['calculation_verified'])
    def test_baseline_migration_rejects_gpu_changes_before_native_work(self):
        api=self.cli();self.setup_baseline(api);self.new['files'][-1]['sha256']='changed'
        with patch.object(api,'verify_saved_package',return_value=self.old),patch.object(api,'open_suite') as opened,self.assertRaisesRegex(ValueError,'canonical source'):api.migrated_development_baseline('coordinate-healing',Path('/source'),self.new['files'],NAME)
        opened.assert_not_called()
    def test_migrated_packet_cannot_start_a_new_gpu_run(self):
        api=self.cli()
        with tempfile.TemporaryDirectory() as tmp:
            capture=Path(tmp)/'capture'
            with patch.object(api,'verify_package',return_value=dict(baseline_migration={'source_package_id':'source'})),patch.object(api,'validate_generation_request') as gate,self.assertRaisesRegex(ValueError,'new GPU execution forbidden'):api.run_capture(capture,'metal',180)
            gate.assert_not_called();self.assertFalse(capture.exists())

if __name__=='__main__':unittest.main()
