"""Transfer-only immutable sharing rejects corruption without executing payloads."""
import importlib.util,json,os,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
s=importlib.util.spec_from_file_location('payload_reuse_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
class PayloadReuseTests(unittest.TestCase):
    def packet(self,path,files):
        m=dict(schema=cli.SCHEMA,suite='future-transfer-only',files=[dict(path=n,bytes=len(b),sha256=cli.sha(b)) for n,b in files.items()]);m['package_id']=cli.package_id(m)
        with zipfile.ZipFile(path,'x') as z:
            z.writestr('gpu-package.json',json.dumps(m))
            for n,b in files.items():z.writestr(n,b)
        return m
    def test_owned_child_imports_source_without_creating_bytecode(self):
        import os,subprocess
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'PYTHONDONTWRITEBYTECODE':'0'}):
            p=Path(directory);(p/'probe_module.py').write_text('value=47\n')
            env=cli.validation_environment(p)
            code='import sys;sys.path.insert(0,sys.argv[1]);import probe_module;print(probe_module.value);print(sys.dont_write_bytecode)'
            r=subprocess.run([sys.executable,'-c',code,str(p)],env=env,capture_output=True,text=True,check=True)
            self.assertEqual(r.stdout.splitlines(),['47','True']);self.assertFalse((p/'__pycache__').exists())
            self.assertEqual(os.environ['PYTHONDONTWRITEBYTECODE'],'0')
    def test_share_only_identical_records_and_never_manifest_or_execute(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);code=b'raise AssertionError("Do not execute payload")';self.packet(p/'a.zip',{'app/x.py':code,'data/a':b'old'})
            cli.unpack(p/'a.zip',p/'a');m=self.packet(p/'b.zip',{'app/x.py':code,'data/a':b'new','data/b':b'added'})
            self.assertEqual(cli.unpack(p/'b.zip',p/'b',reuse_payload_from=p/'a'),m['package_id'])
            self.assertTrue((p/'a/app/x.py').samefile(p/'b/app/x.py'))
            self.assertFalse((p/'a/data/a').samefile(p/'b/data/a'))
            self.assertFalse((p/'a/gpu-package.json').samefile(p/'b/gpu-package.json'))
            cli.check_records(p/'b',m['files'])
    def test_corrupt_reference_and_corrupt_archive_fail_before_destination(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.packet(p/'a.zip',{'member':b'original'});cli.unpack(p/'a.zip',p/'a');(p/'a/member').write_bytes(b'modified')
            with self.assertRaisesRegex(ValueError,'bytes/SHA/size'):cli.unpack(p/'a.zip',p/'b',reuse_payload_from=p/'a')
            self.assertFalse((p/'b').exists())
            with zipfile.ZipFile(p/'bad.zip','x') as z:
                with zipfile.ZipFile(p/'a.zip') as old:
                    z.writestr('gpu-package.json',old.read('gpu-package.json'));z.writestr('member',b'corrupted')
            with self.assertRaisesRegex(ValueError,'integrity'):cli.unpack(p/'bad.zip',p/'c',reuse_payload_from=p/'a')
            self.assertFalse((p/'c').exists())
    def test_symlink_payload_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.packet(p/'a.zip',{'member':b'original'});cli.unpack(p/'a.zip',p/'a');(p/'target').write_bytes(b'original');(p/'a/member').unlink()
            try:(p/'a/member').symlink_to(p/'target')
            except OSError:
                if os.name=='nt':self.skipTest('Windows symlink privilege unavailable')
                raise
            with self.assertRaisesRegex(ValueError,'regular artifact'):cli.unpack(p/'a.zip',p/'b',reuse_payload_from=p/'a')
            self.assertFalse((p/'b').exists())
if __name__=='__main__':unittest.main()
