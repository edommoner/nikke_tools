"""Generic JSON-lines remote process pool; only trusted allow-listed jobs execute."""
from __future__ import annotations

import base64
import concurrent.futures as cf
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import tempfile
import threading
import time
from collections import deque

SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10']


class ConnectionLost(RuntimeError):
    pass


def load_hosts(path):
    hosts = json.loads(Path(path).read_text())
    if not isinstance(hosts, list) or not hosts:
        raise ValueError('Hosts file must be a nonempty JSON array')
    names = {'local'}
    for host in hosts:
        if not isinstance(host, dict) or set(host) != {'name', 'ssh', 'root', 'python', 'env', 'workers'}:
            raise ValueError('Host requires exactly name, ssh, root, python, env, workers')
        for key in ('name', 'ssh', 'root', 'python'):
            if not isinstance(host[key], str) or not host[key] or '\x00' in host[key] or '\n' in host[key]:
                raise ValueError('Invalid host ' + key)
        if not re.fullmatch(r'[A-Za-z0-9._-]+', host['ssh']) or host['ssh'].startswith('-'):
            raise ValueError('Invalid ssh alias')
        if host['name'] in names:
            raise ValueError('Duplicate/reserved host name')
        names.add(host['name'])
        if type(host['workers']) is not int or host['workers'] < 1:
            raise ValueError('Host workers must be positive integer')
        if not isinstance(host['env'], dict) or any(
                not isinstance(k, str) or not re.fullmatch(r'[A-Z0-9_]+', k)
                or not isinstance(v, str) or '\x00' in v or '\n' in v
                for k, v in host['env'].items()):
            raise ValueError('Invalid host env key/value')
    return hosts


def shell_path(path):
    # Tilde inside quotes is literal; expand only the explicitly supported home prefix.
    return '"$HOME"/' + shlex.quote(path[2:]) if path.startswith('~/') else shlex.quote(path)


def worker_command(host):
    env = dict(host['env'], PYTHONDONTWRITEBYTECODE='1')
    return 'cd ' + shell_path(host['root']) + ' && exec env ' + ' '.join(
        shlex.quote(k + '=' + v) for k, v in env.items()) + ' ' + shlex.quote(host['python']) + ' ' + shlex.quote('app/remote_worker.py')


def sync_host(host, root, corpus, cache, namespace):
    """Copy only the execution closure. Never delete or overwrite remote cache entries."""
    root = Path(root)
    subprocess.run([*SSH, host['ssh'], 'mkdir -p ' + shell_path(host['root'])], check=True)
    remote = host['ssh'] + ':' + shell_path(host['root'].rstrip('/') + '/')
    common = ['rsync', '-a', '--exclude=__pycache__', '--exclude=*.pyc', '-e', shlex.join(SSH)]
    subprocess.run([*common, '--relative', 'app/', 'data/', 'gpu/', 'scripts/', 'research/upstream/', remote], cwd=root, check=True)
    target = host['root'].rstrip('/') + '/' + namespace
    subprocess.run([*SSH, host['ssh'], 'mkdir -p ' + shell_path(target + '/cache')], check=True)
    subprocess.run([*common, str(Path(corpus).resolve()), host['ssh'] + ':' + shell_path(target + '/corpus.json')], check=True)
    subprocess.run([*common, '--ignore-existing', str(Path(cache).resolve()) + '/',
                    host['ssh'] + ':' + shell_path(target + '/cache/')], check=True)


def source_hashes(root, paths):
    result = {}
    for path in paths:
        relative = PurePosixPath(path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe native source path')
        result[path] = hashlib.sha256((Path(root) / path).read_bytes()).hexdigest()
    return result


def install_files(files, destinations):
    for item in files:
        relative = PurePosixPath(item['relpath'])
        if relative.is_absolute() or '..' in relative.parts or len(relative.parts) < 2 or relative.parts[0] not in destinations:
            raise ValueError('Unsafe shipped file path')
        target_root = Path(destinations[relative.parts[0]]).resolve()
        target = target_root.joinpath(*relative.parts[1:])
        if not target.resolve().is_relative_to(target_root):
            raise ValueError('Shipped file escapes destination')
        raw = gzip.decompress(base64.b64decode(item['data'], validate=True))
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Shipped file digest mismatch')
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            temporary = Path(stream.name)
        try:
            try:
                os.link(temporary, target)  # Atomic publish-if-absent, including racing publishers.
            except FileExistsError:
                if target.read_bytes() != raw:
                    raise ValueError('Shipped file byte mismatch: ' + str(target))
        finally:
            temporary.unlink()


def file_inventory(destinations):
    return {label + '/' + p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for label, root in destinations.items() for p in Path(root).rglob('*')
            if p.is_file() and not p.name.endswith('.tmp')}


class RemoteHost:
    def __init__(self, host, hello, destinations, transport=None):
        self.host, self.destinations = host, destinations
        self.hello, self.transport = hello, transport
        self.lock = threading.Lock()
        self.pending = {}
        self.seq = 0
        self.closed = False
        self.process = subprocess.Popen(transport or [*SSH, host['ssh'], worker_command(host)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self.info = self._send(dict(type='hello', **hello)).result(timeout=90)
            if self.info['code_identity'] != hello['code_identity'] or self.info['native_hashes'] != hello['native_hashes']:
                raise ValueError('Remote identity mismatch: ' + host['name'])
        except BaseException:
            self.close()
            raise

    def reconnect(self):
        self.close()
        hello = dict(self.hello, known_files=file_inventory(self.destinations))
        return RemoteHost(self.host, hello, self.destinations, self.transport)

    def _send(self, message):
        future = cf.Future()
        with self.lock:
            if self.closed:
                future.set_exception(ConnectionLost('Remote connection closed'))
                return future
            self.seq += 1
            message['seq'] = self.seq
            self.pending[self.seq] = future
            try:
                self.process.stdin.write(json.dumps(message, ensure_ascii=False) + '\n')
                self.process.stdin.flush()
            except (OSError, ValueError) as error:
                self.pending.pop(self.seq)
                future.set_exception(ConnectionLost(str(error)))
        return future

    def submit(self, function, args):
        return self._send(dict(type='job', function=function, args=args))

    def _read(self):
        try:
            for line in self.process.stdout:
                message = json.loads(line)
                with self.lock:
                    future = self.pending.pop(message['seq'])
                try:
                    install_files(message.get('files', []), self.destinations)
                    if 'error' in message:
                        raise RuntimeError(message['error'])
                    future.set_result(message['value'])
                except BaseException as error:
                    future.set_exception(error)
        except BaseException as error:
            reason = str(error)
        else:
            reason = 'worker stdout closed'
        with self.lock:
            self.closed = True
            for future in self.pending.values():
                future.set_exception(ConnectionLost(reason))
            self.pending.clear()

    def close(self):
        if not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=20)
        self.reader.join(timeout=20)
        if not self.process.stdout.closed:
            self.process.stdout.close()


def dispatch(rows, local_pool, local_workers, remotes, local_submit, remote_args, stopped=lambda: False, events=None):
    """Dynamically refill free row slots. Connection failures retry uncommitted rows."""
    queue = deque(rows)
    running = {}
    slots = deque([(None, i) for i in range(local_workers)] +
                  [(remote, i) for remote in remotes for i in range(remote.host['workers'])])
    failures, dropped = {}, set()
    while queue or running:
        if stopped():
            raise InterruptedError('Stop requested; remove STOP to resume')
        while queue and slots:
            remote, index = slots.popleft()
            if remote in dropped:
                continue
            row = queue.popleft()
            future = local_submit(local_pool, row) if remote is None else remote.submit(*remote_args(remote, row))
            running[future] = (row, remote, index, time.perf_counter())
        if not running:
            raise RuntimeError('No worker slots remain to complete pending rows')
        finished, _ = cf.wait(running, timeout=0.5, return_when=cf.FIRST_COMPLETED)
        for future in finished:
            row, remote, index, start = running.pop(future)
            host = remote.host['name'] if remote else 'local'
            try:
                value = future.result()
            except ConnectionLost as error:
                queue.appendleft(row)
                # A single connection failure can affect many slots: count once per connection.
                if remote not in dropped:
                    failures[host] = failures.get(host, 0) + 1
                    dropped.add(remote)
                    event = dict(host=host, failures=failures[host], error=str(error), dropped=failures[host] >= 2)
                    if events is not None:
                        events.append(event)
                    if failures[host] < 2:
                        try:
                            replacement = remote.reconnect()
                        except Exception as reconnect_error:
                            failures[host] += 1
                            event.update(failures=failures[host], dropped=True, reconnect_error=str(reconnect_error))
                        else:
                            remotes.append(replacement)
                            slots.extend((replacement, i) for i in range(replacement.host['workers']))
                    print(json.dumps(dict(remote_failure=event)), flush=True)
                continue
            slots.append((remote, index))
            yield row, value, host, time.perf_counter() - start
