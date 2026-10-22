"""Pipeline growth must not weaken the independent GPU execution deadline."""
import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_backend import run_metal_command,metal_compile_command

@unittest.skipUnless(sys.platform=='darwin','Metal pipe transport is macOS-specific')
class MetalDeadlineTests(unittest.TestCase):
    def test_dispatch_starts_a_fresh_deadline(self):
        code="import sys,time;print('portable_stage=gpu_dispatch',file=sys.stderr,flush=True);time.sleep(1.2);print('done')"
        result=run_metal_command([sys.executable,'-c',code],compile_timeout=1,gpu_timeout=3)
        self.assertEqual((result.returncode,result.stdout.strip()),(0,'done'))
    def test_compile_timeout_is_bounded(self):
        with self.assertRaisesRegex(RuntimeError,'compile phase'):
            run_metal_command([sys.executable,'-c','import time;time.sleep(30)'],compile_timeout=.1,gpu_timeout=3)
    def test_gpu_timeout_is_bounded(self):
        code="import sys,time;print('portable_stage=gpu_dispatch',file=sys.stderr,flush=True);time.sleep(30)"
        with self.assertRaisesRegex(RuntimeError,'gpu phase'):
            run_metal_command([sys.executable,'-c',code],compile_timeout=3,gpu_timeout=.1)
    def test_exit_code_and_both_streams_survive(self):
        result=run_metal_command([sys.executable,'-c',"import sys;print('out');print('error',file=sys.stderr);sys.exit(7)"])
        self.assertEqual((result.returncode,result.stdout.strip(),result.stderr.strip()),(7,'out','error'))
    def test_closed_pipes_do_not_remove_deadline(self):
        with self.assertRaisesRegex(RuntimeError,'compile phase'):
            run_metal_command([sys.executable,'-c','import os,time;os.close(1);os.close(2);time.sleep(30)'],compile_timeout=.1,gpu_timeout=3)


class MetalCacheCommandTests(unittest.TestCase):
    def test_private_cache_is_explicit_without_mutating_callers_argv(self):
        with tempfile.TemporaryDirectory() as folder:
            cache=Path(folder)/'cache';original=['swift','probe.swift','shader.metal']
            actual=metal_compile_command(original,cache)
            self.assertEqual(actual,['swift','-module-cache-path',str(cache),'probe.swift','shader.metal']);self.assertEqual(original,['swift','probe.swift','shader.metal']);self.assertTrue(cache.is_dir())
    def test_relative_cache_is_rejected_and_python_deadline_command_unchanged(self):
        with self.assertRaises(ValueError):metal_compile_command(['swift','probe.swift'],'relative')
        args=[sys.executable,'-c','pass'];self.assertEqual(metal_compile_command(args,'relative'),args)
