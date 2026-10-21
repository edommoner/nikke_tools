"""Fault injection for immutable proof packets, transport integrity and containment hooks."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nikke_gpu_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class PacketTests(unittest.TestCase):
    def test_paths_reject_traversal_windows_drives_and_backslashes(self):
        for path in ('../x','/x','C:/x','a/../x','a\\x','a//b','a/./b'):
            with self.subTest(path=path),self.assertRaises(ValueError):cli.safe_name(path)
        self.assertEqual(cli.safe_name('research/report.json'),'research/report.json')

    def test_collection_export_import_preserves_exact_bytes_without_raw(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);capture=root/'capture';capture.mkdir()
            raw=b'{"passed":true}\r\n';(capture/'evidence.json').write_bytes(raw)
            (capture/'input.bin').write_bytes(b'private raw')
            receipt=cli.collect(capture,capture/'artifacts.json')
            self.assertEqual([r['path'] for r in receipt['files']],['evidence.json'])
            archive=root/'results.zip';cli.export_results(capture,archive)
            result=cli.import_results(archive,root/'import')
            self.assertEqual((root/'import/evidence.json').read_bytes(),raw)
            self.assertEqual(result['gpu_calls'],0);self.assertFalse((root/'import/input.bin').exists())

    def test_export_rejects_changed_original_result(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'result.json').write_text('{}')
            cli.collect(root,root/'artifacts.json');(root/'result.json').write_text('{"passed":true}')
            with self.assertRaises(ValueError):cli.export_results(root,root/'bad.zip')
            self.assertFalse((root/'bad.zip').exists())

    def test_import_rejects_tampering_before_destination_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);receipt=dict(files=[dict(path='x.json',bytes=2,sha256=cli.sha(b'{}'))])
            with zipfile.ZipFile(root/'bad.zip','w') as z:
                z.writestr('artifacts.json',json.dumps(receipt));z.writestr('x.json','[]')
            with self.assertRaises(ValueError):cli.import_results(root/'bad.zip',root/'dest')
            self.assertFalse((root/'dest').exists())

    def test_import_rejects_unlisted_file_and_traversal(self):
        for extra in ('unlisted.json','../escape'):
            with self.subTest(extra=extra),tempfile.TemporaryDirectory() as folder:
                root=Path(folder)
                with zipfile.ZipFile(root/'bad.zip','w') as z:
                    z.writestr('artifacts.json',json.dumps(dict(files=[])));z.writestr(extra,'x')
                with self.assertRaises(ValueError):cli.import_results(root/'bad.zip',root/'dest')
                self.assertFalse((root/'dest').exists())

    def test_file_records_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'a').write_text('{}')
            try:(root/'b').symlink_to(root/'a')
            except OSError:self.skipTest('symlink privilege unavailable')
            with self.assertRaises(ValueError):cli.file_records(root,['b'])

    def test_package_identity_covers_golden_and_source_manifest(self):
        m=dict(schema=1,suite='projectile',files=[],golden=dict(output_sha256='good'))
        identity=cli.package_id(m);m['package_id']=identity
        self.assertEqual(cli.package_id(m),identity)
        m['golden']['output_sha256']='bad';self.assertNotEqual(cli.package_id(m),identity)

    def test_collect_and_import_do_not_import_gpu_backend(self):
        script="""import importlib.util,sys,tempfile,pathlib
s=importlib.util.spec_from_file_location('cli',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d);(p/'result.json').write_text('{}');m.collect(p,p/'artifacts.json');m.export_results(p,p/'r.zip');m.import_results(p/'r.zip',p/'import')
assert 'portable_backend' not in sys.modules
"""
        result=subprocess.run([sys.executable,'-c',script,str(ROOT/'scripts/nikke_gpu.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


class BoundedHooks(unittest.TestCase):
    def module(self):return cli.bounded_module()

    def test_after_wait_runs_inside_wrapper_after_child_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);events=[]
            def before():
                events.append('before');self.assertFalse((root/'start.json').exists())
            def after():
                events.append('after');self.assertTrue((root/'done').exists())
                self.assertFalse((root/'execution.json').exists())
            command=[sys.executable,'-c',"import pathlib,time,sys;p=pathlib.Path(sys.argv[1]);\nwhile not (p/'start.json').exists():time.sleep(.01)\n(p/'done').write_text('done')",str(root)]
            facts=self.module().run_bounded(command,root,10,before_gate=before,after_wait=after)
            self.assertTrue(facts['passed']);self.assertEqual(events,['before','after']);self.assertIsNone(facts['observation_error'])

    def test_snapshot_failure_cannot_skip_cleanup_or_erase_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def fail():raise OSError('snapshot unavailable')
            facts=self.module().run_bounded([sys.executable,'-c','pass'],root,10,after_wait=fail)
            self.assertEqual(facts['final_child_exit_code'],0);self.assertIsNone(facts['cleanup_error'])
            self.assertIn('snapshot unavailable',facts['observation_error']);self.assertTrue((root/'execution.json').exists())

    def test_before_gate_failure_never_releases_child_and_still_observes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);observed=[]
            def fail():raise RuntimeError('preflight failed')
            facts=self.module().run_bounded([sys.executable,'-c','import time;time.sleep(30)'],root,1,before_gate=fail,after_wait=lambda:observed.append(1))
            self.assertFalse((root/'start.json').exists());self.assertFalse(facts['passed'])
            self.assertIsNotNone(facts['final_child_exit_code']);self.assertEqual(observed,[1])

    def test_timeout_still_observes_after_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);observed=[]
            facts=self.module().run_bounded([sys.executable,'-c','import time;time.sleep(30)'],root,1,after_wait=lambda:observed.append(1))
            self.assertTrue(facts['timed_out']);self.assertIsNone(facts['cleanup_error']);self.assertEqual(observed,[1])


if __name__=='__main__':unittest.main()
