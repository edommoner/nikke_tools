#!/usr/bin/env python3
"""Import-clean worker entry point. Stdout is reserved for the JSON-lines protocol."""
from __future__ import annotations

import base64
import concurrent.futures
import contextlib
import gzip
import hashlib
import importlib
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import sys
import threading
import time
import traceback

ALLOW_LIST = {'parity_gate:row_job'}
RESERVE = 20 * 1024**3


def execute(function, args):
    # No calculation/identity module is imported before this fresh spawned task.
    if function not in ALLOW_LIST:
        raise ValueError('Function is not allow-listed: ' + function)
    if shutil.disk_usage(Path.cwd()).free < RESERVE:
        raise RuntimeError('Remote storage reserve requires at least 20 GiB free')
    module, attr = function.split(':')
    if function == 'parity_gate:row_job':
        args[5:8] = [Path(p) for p in args[5:8]]
        os.environ['NIKKE_PARITY_NATIVE_ROOT'] = str(Path.cwd())
    with contextlib.redirect_stdout(sys.stderr):
        return getattr(importlib.import_module(module), attr)(*args)


def snapshot(directories):
    return {label + '/' + p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, p.stat().st_size)
            for label, root in directories.items() for p in root.rglob('*')
            if p.is_file() and not p.name.endswith('.tmp')}


def main():
    for key, value in tuple(os.environ.items()):
        if value.startswith('~/'):
            os.environ[key] = os.path.expanduser(value)
    pool = None
    lock = threading.Lock()
    directories, reported = {}, {}

    def send(seq, value=None, error=None, files=None):
        message = dict(type='result', seq=seq, files=files or [])
        message.update(error=error) if error is not None else message.update(value=value)
        print(json.dumps(message, ensure_ascii=False), flush=True)

    def completed(seq, future, started):
        with lock:
            files = []
            try:
                current = snapshot(directories)
                for relpath, stamp in current.items():
                    if reported.get(relpath) == stamp:
                        continue
                    label, relative = relpath.split('/', 1)
                    raw = (directories[label] / relative).read_bytes()
                    files.append(dict(relpath=relpath, data=base64.b64encode(gzip.compress(raw, mtime=0)).decode(),
                                      sha256=hashlib.sha256(raw).hexdigest()))
                reported.update(current)
                value = future.result()
                send(seq, value=value, files=files)
            except BaseException:
                send(seq, error=traceback.format_exc(), files=files)

    try:
        for line in sys.stdin:
            message = json.loads(line)
            seq = message['seq']
            try:
                if message['type'] == 'hello':
                    if pool is not None:
                        raise ValueError('Duplicate hello')
                    root = Path.cwd().resolve()
                    namespace = Path(message['namespace'])
                    if namespace.is_absolute() or '..' in namespace.parts or namespace.parts[:3] != ('research', 'parity', 'remote-pool'):
                        raise ValueError('Unsafe remote namespace')
                    directories.update({label: root / namespace / label for label in ('cache', 'native')})
                    for path in [*directories.values(), root / namespace / 'scratch']:
                        path.mkdir(parents=True, exist_ok=True)
                    # Imports happen only in the coordinator, never in spawned task interpreters.
                    import parity_gate
                    from remote_pool import source_hashes
                    from portable_slang_generation import slang_compiler
                    from portable_native import clang_compiler
                    import subprocess
                    info = dict(code_identity=parity_gate.code_identity(root)[0],
                                native_hashes=source_hashes(root, message['native_sources']),
                                slangc=subprocess.check_output([str(slang_compiler(root)), '-version'], stderr=subprocess.STDOUT, text=True),
                                clang=subprocess.check_output([clang_compiler(), '--version'], text=True))
                    for relpath, stamp in snapshot(directories).items():
                        label, relative = relpath.split('/', 1)
                        if message.get('known_files', {}).get(relpath) == hashlib.sha256((directories[label] / relative).read_bytes()).hexdigest():
                            reported[relpath] = stamp
                    pool = concurrent.futures.ProcessPoolExecutor(max_workers=message['workers'],
                        max_tasks_per_child=1, mp_context=multiprocessing.get_context('spawn'))
                    send(seq, value=info)
                elif message['type'] == 'job':
                    if pool is None:
                        raise ValueError('hello required')
                    if message['function'] not in ALLOW_LIST:
                        raise ValueError('Function is not allow-listed: ' + message['function'])
                    future = pool.submit(execute, message['function'], message['args'])
                    future.add_done_callback(lambda f, seq=seq: completed(seq, f, time.perf_counter()))
                else:
                    raise ValueError('Unknown message type')
            except BaseException:
                with lock:
                    send(seq, error=traceback.format_exc())
    finally:
        if pool:
            pool.shutdown(wait=True, cancel_futures=True)


if __name__ == '__main__':
    main()
