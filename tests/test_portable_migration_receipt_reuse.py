import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_migration_receipt_reuse import reuse

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);p=Path(self.tmp.name)
        self.root=p/'new';self.source=p/'old';self.capture=p/'capture'
        for d in [self.root,self.source,self.capture]:d.mkdir()
        self.current=self.payload(self.root);self.old=self.payload(self.source)
        for name in ['reference-migration.json','artifacts.json']:(self.capture/name).write_text('{}')
        self.name='coordinate-healing-routed-adds-v1';(self.capture/'replay.json').write_text(json.dumps(dict(reference_migration=self.name,source_package=str(self.source))))
        self.calls=[]
        def original(*args):self.calls.append(args);return dict(verified=True)
        self.original=original;self.module=SimpleNamespace(ROOT=self.root,verify_reference_migration=original,check_records=self.check)
    def payload(self,path):
        (path/'payload.py').write_text('frozen');m=dict(files=[dict(path='payload.py',sha256=hashlib.sha256(b'frozen').hexdigest())]);(path/'gpu-package.json').write_text(json.dumps(m));return m
    def check(self,root,rows):
        for r in rows:
            if hashlib.sha256((root/r['path']).read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Payload changed')
    def test_only_metadata_is_reused_and_results_are_not_shared_mutable_objects(self):
        with reuse(self.module,self.capture) as stats:
            first=self.module.verify_reference_migration(self.name,self.old,self.current);first['verified']=False
            second=self.module.verify_reference_migration(self.name,self.old,self.current)
        self.assertTrue(second['verified']);self.assertEqual(len(self.calls),1);self.assertEqual(stats,dict(fresh_checks=1,reused_checks=1,native_comparison_reuse=False));self.assertIs(self.module.verify_reference_migration,self.original)
    def test_payload_or_anchor_changes_cannot_reuse_a_receipt(self):
        for path in [self.root/'payload.py',self.source/'payload.py',self.capture/'reference-migration.json']:
            before=path.read_bytes()
            with self.subTest(path=path),reuse(self.module,self.capture):
                self.module.verify_reference_migration(self.name,self.old,self.current);path.write_text('changed')
                with self.assertRaises(ValueError):self.module.verify_reference_migration(self.name,self.old,self.current)
            path.write_bytes(before)
    def test_different_arguments_are_rejected_and_unknown_migrations_are_not_cached(self):
        with reuse(self.module,self.capture):
            self.module.verify_reference_migration(self.name,self.old,self.current)
            with self.assertRaisesRegex(ValueError,'context changed'):self.module.verify_reference_migration(self.name,self.old,{**self.current,'changed':True})
            self.module.verify_reference_migration('other',self.old,self.current);self.module.verify_reference_migration('other',self.old,self.current)
        self.assertEqual(len(self.calls),3)
    def prepare_module(self):
        self.preparations=[]
        def prepare(adapter,manifest):self.preparations.append(adapter);return ([dict(owner=0)],b'fresh input')
        self.module.prepare_entries=prepare;return SimpleNamespace(__file__='/frozen/adapter.py')
    def test_static_preparation_is_fresh_once_without_caching_native_results(self):
        adapter=self.prepare_module()
        with reuse(self.module,self.capture) as stats:
            first=self.module.prepare_entries(adapter,self.current)
            self.module.verify_reference_migration(self.name,self.old,self.current)
            second=self.module.prepare_entries(SimpleNamespace(__file__=adapter.__file__),self.current)
        self.assertIs(first,second);self.assertEqual(len(self.preparations),1);self.assertEqual(stats['fresh_input_preparations'],1);self.assertEqual(stats['reused_input_preparations'],1);self.assertFalse(stats['native_comparison_reuse'])
    def test_mutated_domain_cannot_be_reused(self):
        adapter=self.prepare_module()
        with reuse(self.module,self.capture):
            entries,_=self.module.prepare_entries(adapter,self.current)
            self.module.verify_reference_migration(self.name,self.old,self.current);entries[0]['owner']=1
            with self.assertRaisesRegex(ValueError,'domain changed'):self.module.prepare_entries(adapter,self.current)
    def test_preparation_requires_same_adapter_manifest_and_completed_validation(self):
        adapter=self.prepare_module()
        with reuse(self.module,self.capture):
            self.module.prepare_entries(adapter,self.current)
            with self.assertRaisesRegex(ValueError,'completed migration'):self.module.prepare_entries(adapter,self.current)
            self.module.verify_reference_migration(self.name,self.old,self.current)
            for other,manifest in [(SimpleNamespace(__file__='/other.py'),self.current),(adapter,{**self.current,'changed':True})]:
                with self.assertRaisesRegex(ValueError,'domain changed'):self.module.prepare_entries(other,manifest)

if __name__=='__main__':unittest.main()
