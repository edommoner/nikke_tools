"""Remote protocol tests use local subprocesses, never SSH or installation."""
import base64
import concurrent.futures as cf
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import parity_gate as gate
import remote_pool as remote


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root with spaces'
        self.app = self.root / 'app'
        self.app.mkdir(parents=True)
        for name in ('remote_pool.py', 'remote_worker.py', 'parity_gate.py', 'portable_native.py', 'portable_slang_generation.py'):
            shutil.copyfile(gate.ROOT / 'app' / name, self.app / name)
        (self.app / 'engine_worker.py').write_text('# minimal CPU closure\n')
        (self.root / gate.ENGINE / 'calculator').mkdir(parents=True)
        compiler = self.root / 'slang/bin/slangc'
        compiler.parent.mkdir(parents=True)
        compiler.write_text('#!/bin/sh\nprintf "test slang\\n"\n')
        compiler.chmod(0o755)
        (self.app / 'test_jobs.py').write_text('''from pathlib import Path
import os

def echo(value):
    return value

def ship(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
    return {'shipped': value}

def die():
    os._exit(7)
''')
        # The test-only extension is repeated by spawn when it imports the launcher.
        launcher = self.app / 'test_launcher.py'
        launcher.write_text('''import remote_worker as worker
worker.ALLOW_LIST.update({'test_jobs:echo', 'test_jobs:ship', 'test_jobs:die'})
if __name__ == '__main__':
    worker.main()
''')
        self.host = dict(name='test', ssh='gx10-afe7-tailscale', root=str(self.root),
                         python=sys.executable, env={}, workers=2)
        self.namespace = 'research/parity/remote-pool/test'
        self.destinations = {k: Path(self.temp.name) / 'coordinator' / k for k in ('cache', 'native')}
        self.hello = dict(namespace=self.namespace, workers=2, code_identity=gate.code_identity(self.root)[0],
                          native_sources=['app/engine_worker.py'],
                          native_hashes=remote.source_hashes(self.root, ['app/engine_worker.py']), known_files={})
        # env and cwd are confined to this child; transport bypasses SSH entirely.
        self.transport = ['env', 'PYTHONDONTWRITEBYTECODE=1', 'NIKKE_SLANG_ROOT=' + str(self.root / 'slang'),
                          sys.executable, '-c',
                          'import os,runpy,sys;os.chdir(sys.argv[1]);sys.path.insert(0,"app");runpy.run_path("app/test_launcher.py",run_name="__main__")', str(self.root)]

    def connect(self, hello=None):
        client = remote.RemoteHost(self.host, hello or self.hello, self.destinations, self.transport)
        self.addCleanup(client.close)
        return client

    def test_roundtrip_and_allow_list(self):
        client = self.connect()
        futures = [client.submit('test_jobs:echo', [dict(index=i)]) for i in range(4)]
        self.assertEqual([f.result(timeout=20) for f in futures], [dict(index=i) for i in range(4)])
        with self.assertRaisesRegex(RuntimeError, 'not allow-listed'):
            client.submit('os:system', ['echo forbidden']).result(timeout=20)

    def test_file_shipping_and_reconnect_inventory(self):
        client = self.connect()
        path = self.root / self.namespace / 'cache/a/entry.gz'
        self.assertEqual(client.submit('test_jobs:ship', [str(path), 'payload']).result(timeout=20), {'shipped': 'payload'})
        target = self.destinations['cache'] / 'a/entry.gz'
        self.assertEqual(target.read_text(), 'payload')
        client.submit('test_jobs:ship', [str(path), 'payload']).result(timeout=20)
        target.write_text('conflict')
        with self.assertRaisesRegex(ValueError, 'byte mismatch'):
            client.submit('test_jobs:ship', [str(path), 'payload']).result(timeout=20)

    def test_existing_unreported_files_ship_after_reconnect(self):
        path = self.root / self.namespace / 'native/1.json.gz'
        path.parent.mkdir(parents=True)
        path.write_text('saved before connection loss')
        client = self.connect()
        client.submit('test_jobs:echo', ['ok']).result(timeout=20)
        self.assertEqual((self.destinations['native'] / '1.json.gz').read_text(), path.read_text())

    def test_identity_mismatch_refused(self):
        for key in ('code_identity', 'native_hashes'):
            hello = dict(self.hello, **{key: 'wrong' if key == 'code_identity' else {}})
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                self.connect(hello)

    def test_death_retries_inflight_locally(self):
        client = self.connect()
        events = []
        # Real subprocess death, with an initial local row occupying the local slot.
        def local_submit(pool, row):
            def work():
                import time
                time.sleep(.2)
                return row
            return pool.submit(work)
        original = client.submit
        def submit(function, args):
            future = original(function, args)
            client.process.kill()
            return future
        client.submit = submit
        # Model a second failed connection attempt: the host is then dropped.
        client.reconnect = lambda: (_ for _ in ()).throw(remote.ConnectionLost('reconnect failed'))
        with cf.ThreadPoolExecutor(max_workers=1) as pool:
            results = list(remote.dispatch([1, 2, 3], pool, 1, [client], local_submit,
                lambda host, row: ('test_jobs:echo', [row]), events=events))
        self.assertEqual(sorted(r[1] for r in results), [1, 2, 3])
        self.assertTrue(all(r[2] == 'local' for r in results))
        self.assertEqual(events[0]['failures'], 2)
        self.assertTrue(events[0]['dropped'])

    def test_hosts_validation(self):
        path = Path(self.temp.name) / 'hosts.json'
        path.write_text(json.dumps([self.host]))
        self.assertEqual(remote.load_hosts(path), [self.host])
        for mutation in ({'ssh': '-oProxyCommand=bad'}, {'ssh': '-V'}, {'unknown': 1}, {'env': {'bad-key': 'x'}},
                         {'workers': True}, {'workers': 0}, {'root': 1}, {'env': []}, {'name': 'local'}):
            path.write_text(json.dumps([dict(self.host, **mutation)]))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                remote.load_hosts(path)

    def test_shell_quoting(self):
        host = dict(self.host, root=str(self.root), env={'VALUE': "literal ' $(touch forbidden)"})
        # Replace the executable with a shell-script fixture to inspect cwd/env.
        executable = self.root / 'python fixture'
        executable.write_text('#!/bin/sh\nprintf "%s\\n%s\\n" "$PWD" "$VALUE"\n')
        executable.chmod(0o755)
        host['python'] = str(executable)
        result = subprocess.check_output(['sh', '-c', remote.worker_command(host)], text=True)
        self.assertEqual(result.splitlines(), [str(self.root), host['env']['VALUE']])
        self.assertFalse((self.root / 'forbidden').exists())
        self.assertEqual(remote.shell_path('~/root with spaces'), '"$HOME"/\'root with spaces\'')

    def test_sync_scope_and_cache_policy(self):
        with patch.object(remote.subprocess, 'run') as run:
            remote.sync_host(self.host, self.root, self.root / 'corpus.json',
                             self.root / 'cache', self.namespace)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertTrue(all('--delete' not in command for command in commands))
        self.assertIn('--ignore-existing', commands[-1])
        self.assertIn('--relative', commands[1])
        for path in ('app/', 'data/', 'gpu/', 'scripts/', 'research/upstream/'):
            self.assertIn(path, commands[1])
        for command in (commands[0], commands[2]):
            self.assertEqual(command[:5], remote.SSH)
        self.assertIn("'", commands[1][-1])  # Remote root with spaces is quoted.

    def test_shipped_paths_and_hashes(self):
        raw = b'payload'
        item = dict(relpath='cache/a', data=base64.b64encode(gzip.compress(raw)).decode(), sha256=hashlib.sha256(raw).hexdigest())
        remote.install_files([item], self.destinations)
        remote.install_files([item], self.destinations)
        for mutation in ({'relpath': 'cache/../escape'}, {'relpath': '/absolute'}, {'sha256': 'wrong'}):
            with self.assertRaises(ValueError):
                remote.install_files([dict(item, **mutation)], self.destinations)


if __name__ == '__main__':
    unittest.main()
