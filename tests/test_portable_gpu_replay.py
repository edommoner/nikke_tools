"""Replay accepts a completed dispatch, never changed sources or control failure."""
import copy
from types import SimpleNamespace
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('replay_cli_tests',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.package=root/'package';self.package.mkdir();self.capture=root/'capture';self.capture.mkdir()
        critical=['app/portable_backend.py','app/portable_compile_cache.py','scripts/run-metal-probe.swift',
          'research/portable_phase_audit.py','research/summarize-portable-cross-gpu.py',
          'app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py',
          'gpu/entry.slang','research/upstream/native.py']
        self.old=dict(package_id='original',purpose='development',suite='recipients',golden=dict(source='fixed',input='fixed',native='fixed'),
                      files=[dict(path=p,sha256='fixed') for p in critical])
        self.new=copy.deepcopy(self.old);self.new['package_id']='new'
        cli.write(self.package/'gpu-claimed-metal.json',dict(package_id='original',capture=str(self.capture)))
        cli.write(self.capture/'run.json',dict(package_id='original',backend='metal',mode='gpu'))
        self.facts=dict(passed=False,timed_out=False,error=None,cleanup_error=None,observation_error=None,final_child_exit_code=1)
        cli.write(self.capture/'execution.json',self.facts)
        cli.write(self.capture/'evidence.json',dict(backend='metal',gpu_execution_verified=True,
            transport=dict(command_status='completed'),generated_sha256=dict(cuda=cli.sha(b'cuda'),metal=cli.sha(b'metal'))))
        (self.capture/'generated.cu').write_bytes(b'cuda');(self.capture/'generated.metal').write_bytes(b'metal')
        (self.capture/'phases.jsonl').write_text('{"stage":"shared_gpu_execute","state":"entered"}\n{"stage":"shared_gpu_execute","state":"returned"}\n')
        cli.write(self.capture/'comparison.json',dict(calculation_verified=False));cli.write(self.capture/'result.json',dict(passed=False))
        self.collect()

    def collect(self):cli.collect(self.capture,self.capture/'artifacts.json')
    def check(self):
        with patch.object(cli,'verify_package',return_value=self.old):return cli.replay_source(self.new,self.package,self.capture)

    def test_completed_dispatch_with_old_decoder_failure_preserves_failure(self):
        _,facts,_=self.check();self.assertFalse(facts['passed']);self.assertEqual(facts['final_child_exit_code'],1)

    def test_replay_publishes_the_single_fresh_comparison_and_keeps_original_failure(self):
        (self.capture/'input.bin').write_bytes(b'input');(self.capture/'readback.bin').write_bytes(b'raw')
        destination=self.capture.parent/'replay'
        comparison=dict(calculation_verified=False,mismatches=[dict(reason='Still differs')],entries=[])
        def source(*args):return self.old,self.facts,cli.load(self.capture/'evidence.json')
        before=(self.capture/'comparison.json').read_bytes()
        with patch.object(cli,'verify_package',return_value=self.new),patch.object(cli,'replay_source',side_effect=source),\
             patch.object(cli,'compare_readback',return_value=comparison) as compare,\
             patch('portable_capture_storage.shutil.disk_usage',return_value=SimpleNamespace(free=2**40)):
            result=cli.replay_capture(destination,self.package,self.capture)
        compare.assert_called_once_with(self.new,destination)
        self.assertFalse(result['passed']);self.assertEqual(result['gpu_calls'],0)
        self.assertEqual(cli.load(destination/'comparison.json'),comparison)
        self.assertEqual((self.capture/'comparison.json').read_bytes(),before)
        self.assertEqual(cli.load(destination/'source-execution.json'),self.facts)

    def test_input_native_or_source_baseline_changes_are_rejected(self):
        for key in ('source','input','native'):
            with self.subTest(key=key):
                self.new['golden'][key]='changed'
                with self.assertRaisesRegex(ValueError,'baselines'):self.check()
                self.new['golden'][key]='fixed'

    def test_runtime_and_newly_added_gpu_or_native_files_are_rejected(self):
        self.new['files'][0]['sha256']='changed'
        with self.assertRaisesRegex(ValueError,'changed'):self.check()
        self.new=copy.deepcopy(self.old)
        for path in ('gpu/new.slang','research/upstream/new.py','app/portable_slang_generation.py'):
            self.new['files'].append(dict(path=path,sha256='new'))
            with self.assertRaisesRegex(ValueError,'changed'):self.check()
            self.new['files'].pop()

    def test_timeout_cleanup_and_incomplete_dispatch_are_rejected(self):
        for key,value in [('timed_out',True),('cleanup_error','timeout'),('observation_error','failed')]:
            facts=dict(self.facts,**{key:value});cli.write(self.capture/'execution.json',facts);self.collect()
            with self.assertRaisesRegex(ValueError,'control failure'):self.check()
        cli.write(self.capture/'execution.json',self.facts)
        (self.capture/'phases.jsonl').write_text('{"stage":"shared_gpu_execute","state":"entered"}\n');self.collect()
        with self.assertRaisesRegex(ValueError,'boundary incomplete'):self.check()

    def test_changed_generated_bytes_and_original_failure_records_are_rejected(self):
        (self.capture/'generated.cu').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'generated bytes'):self.check()
        (self.capture/'generated.cu').write_bytes(b'cuda')
        cli.write(self.capture/'result.json',dict(passed=True))
        with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main()
