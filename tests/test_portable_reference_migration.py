import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_reference_migration import NAME,CASE,SOURCES,digest,verify
class ReferenceMigrationTests(unittest.TestCase):
    def setUp(self):
        self.reference=dict(battle=dict(graph_states=[[0,2,0,0,0,0,1]],damage=[8000]),skill_trace=[])
        prior=copy.deepcopy(self.reference);prior['battle']['graph_states'][0][6]=0
        self.old=dict(suite='parts-skill-world',files=[dict(path=p,sha256=v[0]) for p,v in SOURCES.items()],golden=dict(source_sha256={'gpu/source':'fixed'},input_sha256='fixed',entries=[dict(name=CASE,input_sha256='fixed',native_sha256=digest(prior))]))
        self.new=copy.deepcopy(self.old)
        for row in self.new['files']:row['sha256']=SOURCES[row['path']][1]
        self.new['golden']['entries'][0]['native_sha256']=digest(self.reference)
    def test_only_the_named_observation_change_is_admitted(self):
        receipt=verify(NAME,self.old,self.new,self.reference)
        self.assertTrue(receipt['all_other_native_fields_equal']);self.assertEqual(receipt['gpu_calls'],0)
    def test_other_native_state_lifetime_input_source_or_case_changes_reject(self):
        for what in ('damage','lifetime','input','gpu','observer','case'):
            new=copy.deepcopy(self.new);ref=copy.deepcopy(self.reference)
            if what=='damage':ref['battle']['damage'][0]+=1;new['golden']['entries'][0]['native_sha256']=digest(ref)
            if what=='lifetime':ref['battle']['graph_states'][0][1]=1
            if what=='input':new['golden']['input_sha256']='changed'
            if what=='gpu':new['golden']['source_sha256']['gpu/source']='changed'
            if what=='observer':new['files'][0]['sha256']='changed'
            if what=='case':new['golden']['entries'][0]['name']='different'
            with self.subTest(what=what),self.assertRaises(ValueError):verify(NAME,self.old,new,ref)
    def test_unknown_migration_or_suite_reject(self):
        with self.assertRaises(ValueError):verify('generic',self.old,self.new,self.reference)
        self.new['suite']='another'
        with self.assertRaises(ValueError):verify(NAME,self.old,self.new,self.reference)
