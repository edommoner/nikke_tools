"""Exercise the CPU-only maintenance CLI against synthetic evidence only."""
import contextlib
import importlib.util
import io
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/nikke_storage.py'
COMMANDS = ('benchmark-inventory', 'archive-benchmarks', 'benchmark-status',
            'restore-benchmark', 'reclaim-project')


class StorageMaintenanceCLITests(unittest.TestCase):
    def run_cli(self, *args, ok=True):
        # Process observation is a controlled dependency in these fixture tests.
        # Production ensure_idle still runs and fails closed if ps is unavailable.
        spec = importlib.util.spec_from_file_location('storage_cli_test', CLI)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        import portable_benchmark_storage as storage
        actual = storage.subprocess.check_output
        def observe(command, *a, **kw):
            if command == ['ps', '-axo', 'pid=,command=']:
                return ''
            return actual(command, *a, **kw)
        stdout, stderr = io.StringIO(), io.StringIO()
        code = 0
        with patch.object(sys, 'argv', [str(CLI), *map(str, args)]), \
             patch.object(storage.subprocess, 'check_output', side_effect=observe), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                cli.main()
            except SystemExit as error:
                code = error.code
            except (ValueError, OSError) as error:
                code = 1
                stderr.write(str(error))
        result = subprocess.CompletedProcess(args, code, stdout.getvalue(), stderr.getvalue())
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def fixture(self, root):
        repo = root / 'repo'
        capture = repo / 'research/portable-build/example/work-0'
        capture.mkdir(parents=True)
        evidence = dict(transport={})
        originals = {}
        for name, key, sizekey in [('input.bin', 'input_sha256', 'input_bytes'),
                                   ('readback.bin', 'output_sha256', 'output_bytes')]:
            data = b'HEADER' + bytes(2 * 1024**2) + name.encode()
            path = capture / name
            path.write_bytes(data)
            os.utime(path, (time.time() - 90000,) * 2)
            originals[path.relative_to(repo).as_posix()] = data
            evidence[key] = hashlib.sha256(data).hexdigest()
            evidence['transport'][sizekey] = len(data)
        (capture / 'evidence.json').write_text(json.dumps(evidence))
        report = dict(passed=True, samples=[dict(captured=str(capture),
                       input_sha256=evidence['input_sha256'],
                       output_sha256=evidence['output_sha256'])])
        (repo / 'research/example-benchmark.json').write_text(json.dumps(report))
        return repo, originals

    def test_help_and_invalid_options(self):
        self.run_cli('--help')
        for command in COMMANDS:
            self.run_cli(command, '--help')
        self.run_cli('archive-benchmarks', '--storage', 'unused', '--remove-original', ok=False)
        self.run_cli('benchmark-inventory', '--storage', 'unused', '--folder', 'unpaired', ok=False)
        self.run_cli('reclaim-project', '--storage', 'unused', '--limit', '0', ok=False)

    def test_plan_archive_restore_and_integrity_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, originals = self.fixture(root)
            storage = root / 'archives'
            common = ['--repository', repo, '--storage', storage]
            self.run_cli('benchmark-inventory', *common, '--folder', 'example',
                         '--report', 'example-benchmark.json')
            before = {p.relative_to(storage): p.read_bytes() for p in storage.rglob('*') if p.is_file()}
            result = self.run_cli('archive-benchmarks', *common)
            self.assertFalse(json.loads(result.stdout)['apply'])
            self.assertEqual(before, {p.relative_to(storage): p.read_bytes() for p in storage.rglob('*') if p.is_file()})
            for name, data in originals.items():
                self.assertEqual((repo / name).read_bytes(), data)
            self.run_cli('archive-benchmarks', *common, '--apply')
            for name, data in originals.items():
                self.assertEqual((repo / name).read_bytes(), data)
            self.run_cli('storage-check', '--path', repo, '--storage', storage, '--require-archived', ok=False)
            self.run_cli('archive-benchmarks', *common, '--apply', '--remove-original')
            self.run_cli('storage-check', '--path', repo, '--storage', storage, '--require-archived', '--verify')
            for name, data in originals.items():
                self.assertFalse((repo / name).exists())
                self.run_cli('restore-benchmark', *common, '--path', name)
                self.assertEqual((repo / name).read_bytes(), data)
                self.run_cli('restore-benchmark', *common, '--path', name, ok=False)
            self.run_cli('benchmark-status', *common, '--verify')

    @unittest.skipUnless(sys.platform == 'darwin', 'Darwin zero-block reclamation')
    def test_reclaim_plan_preserves_raw_allocation_bytes_and_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, originals = self.fixture(root)
            before = {name: ((repo / name).stat().st_blocks, (repo / name).stat().st_mtime_ns)
                      for name in originals}
            self.run_cli('reclaim-project', '--repository', repo, '--storage', root / 'plan')
            receipts = [json.loads(p.read_text()) for p in (root / 'plan').glob('*.json')]
            summary = next(r for r in receipts if 'files' in r)
            self.assertEqual(summary['files'], 2)
            self.assertEqual(summary['reclaimed_bytes'], 0)
            self.assertGreater(summary['zero_range_bytes'], 0)
            for name, data in originals.items():
                self.assertEqual((repo / name).read_bytes(), data)
                info = (repo / name).stat()
                self.assertEqual((info.st_blocks, info.st_mtime_ns), before[name])
            self.run_cli('reclaim-project', '--repository', repo, '--storage', root / 'plan', '--apply', ok=False)


if __name__ == '__main__':
    unittest.main()
