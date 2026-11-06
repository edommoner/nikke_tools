"""S20 sealed truth collection. No L2 imports or predictions in this module.

Native collection delegates unchanged to S9 (32-row batches, ten host threads,
deferred verification, forbidden CPU fallback, owned transient captures only).
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import threading
import time

import measure_s9 as s9

SEED = 200020
RESERVE = int(20.5 * 1024**3)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare(out, profiles):
    excluded = {tuple(r['members']) for f in ('s9-dataset.jsonl', 's9-search.jsonl', 's1-results.jsonl')
                for r in s9.read(s9.HERE / f)}
    p = json.loads(profiles.read_text())
    for c in p['characters'].values():
        excluded.update(tuple(s) for s in c['standard_squads'])
    rows = [dict(id=i, members=list(s)) for i, s in
            enumerate(s9.generate(3000, SEED, excluded))]
    save(out / 'selection.json', dict(seed=SEED, excluded_count=len(excluded), rows=rows))
    body = json.loads(Path(s9.INPUT['benchmark']).read_text())[0]
    body.update(s9.INPUT['settings'])
    save(out / 'bodies.json', [body])


def collect(out):
    if not str(s9.ROOT).startswith('/home/'):
        raise RuntimeError('Detailed collection is gx10-only')
    if shutil.disk_usage(out).free < RESERVE + 2 * 1024**3:
        raise RuntimeError('Insufficient storage reserve and peak budget')
    started = time.perf_counter()
    stop = threading.Event()
    samples = []

    def monitor():
        while not stop.is_set():
            free = shutil.disk_usage(out).free
            samples.append(dict(time=time.time(), free_bytes=free))
            save(out / 'storage.json', dict(samples=samples, min_free=min(x['free_bytes'] for x in samples)))
            if free < RESERVE:
                os._exit(3)
            stop.wait(10)

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    try:
        s9.SCRATCH = out
        s9.INPUT['benchmark'] = str(out / 'bodies.json')
        # Reuse existing warm caches without copying hundreds of MB. Remote
        # writes remain within ~/nikke-remote; no pre-existing files are removed.
        (out / 'cache').mkdir(exist_ok=True)
        for name in ('cpp', 'native'):
            dst = out / 'cache' / name
            if not dst.exists():
                dst.symlink_to(s9.ROOT / 'research/portable-build' / name, target_is_directory=True)
        rows = json.loads((out / 'selection.json').read_text())['rows']
        s9.evaluate(rows, out / 'native-journal.jsonl')
        raw = s9.read(out / 'native-journal.jsonl')
        if len(raw) != 3000 or len({r['id'] for r in raw}) != 3000:
            raise RuntimeError('Incomplete sealed collection')
        target = out / 's20-sealed.jsonl'
        if target.exists():
            raise RuntimeError('Refusing to replace a sealed file')
        failures = []
        with target.open('x') as f:
            for r in raw:
                ok = r['backend'] == 'native_detail' and (r.get('total_damage') or 0) > 0
                reason = r.get('fallback_reason') or r.get('error') or r.get('unsupported')
                status = 'ok' if ok else dict(failed=reason or 'Missing positive native total')
                row = dict(id=r['id'], members=r['members'], total=r.get('total_damage'),
                           backend=r['backend'], status=status)
                if not ok:
                    failures.append(dict(id=r['id'], reason=status))
                f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
            f.flush()
            os.fsync(f.fileno())
        save(out / 'seal.json', dict(sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
             sealed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), rows=3000,
             native_successes=3000-len(failures), failures=failures, seed=SEED,
             host=socket.gethostname(), wall_seconds=time.perf_counter()-started,
             verification='deferred', L2_scored=False))
    finally:
        stop.set()
        thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'collect'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--profiles', type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.action == 'prepare':
        prepare(args.out, args.profiles)
    else:
        collect(args.out)
