"""Saved CUDA compiler ownership uses its own immutable compact registry."""
import copy,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_package_projection import project,roots_for,validate,validate_historical
s=importlib.util.spec_from_file_location('historical_projection_test_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class HistoricalProjectionTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.config=dict(script='research/old.py',tests=['test_old.py']);self.smoke=['test_owned_smoke.py']
        code="""import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
SUITES={'resident-frames-device':{'script':'research/old.py','tests':['test_old.py']}}
SMOKE_TESTS=['test_owned_smoke.py']
def package_id(m):return hashlib.sha256(json.dumps({k:v for k,v in m.items() if k!='package_id'},sort_keys=True,separators=(',',':')).encode()).hexdigest()
def native_reference(*a):raise AssertionError('Native execution forbidden')
"""
        files={'scripts/nikke_gpu.py':code,'app/portable_package_projection.py':(ROOT/'app/portable_package_projection.py').read_text(),
            'research/old.py':'pass\n','tests/test_old.py':'pass\n','tests/test_owned_smoke.py':'pass\n',
            'research/run-world-bounded.py':'pass\n','research/portable_phase_audit.py':'pass\n','research/summarize-portable-cross-gpu.py':'pass\n'}
        for n,text in files.items():
            p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        names,projection=project(self.root,files,roots_for(self.config,self.smoke))
        self.m=dict(schema=cli.SCHEMA,suite='resident-frames-device',files=cli.file_records(self.root,names),payload_projection=projection)
        self.m['package_id']=cli.package_id(self.m);cli.write(self.root/'gpu-package.json',self.m)
    def test_current_tests_cannot_reinterpret_old_successful_package(self):
        with self.assertRaises(ValueError):validate(self.m['payload_projection'],self.m['files'],self.m['suite'],self.config,['test_new.py'])
        cli.check_records(self.root,self.m['files'])
        before=cli.file_records(self.root,[r['path'] for r in self.m['files']])
        result=validate_historical(self.root,self.m,cli)
        self.assertTrue(result['projection_verified']);self.assertEqual(result['gpu_calls'],0);self.assertEqual(result['native_calls'],0)
        self.assertEqual(before,cli.file_records(self.root,[r['path'] for r in self.m['files']]))
    def test_unverified_registry_bytes_are_rejected_before_subprocess(self):
        p=self.root/'scripts/nikke_gpu.py';p.write_text(p.read_text()+'\n# changed\n')
        with patch('subprocess.run',side_effect=AssertionError('Do not execute unverified owner')),self.assertRaisesRegex(ValueError,'verified payload'):
            validate_historical(self.root,self.m,cli)
    def test_invalid_old_projection_is_not_accepted_as_historical(self):
        self.m['payload_projection']['roots'].pop();self.m['package_id']=cli.package_id(self.m);cli.write(self.root/'gpu-package.json',self.m)
        with self.assertRaises(subprocess.CalledProcessError):validate_historical(self.root,self.m,cli)
    def test_registry_mutation_during_child_is_rejected(self):
        run=subprocess.run
        def changed(*a,**kw):
            result=run(*a,**kw);p=self.root/'scripts/nikke_gpu.py';p.write_text(p.read_text()+'\n# late change\n');return result
        with patch('subprocess.run',side_effect=changed),self.assertRaisesRegex(ValueError,'ownership changed'):
            validate_historical(self.root,self.m,cli)


if __name__=='__main__':unittest.main()
