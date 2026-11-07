"""S23 sequential timings with an idle gate and a storage floor.

Use --phase baseline before editing the core, then --phase after. Evidence is
append-only; completed job identities are reused on coordinator restart.
"""
import argparse
import ctypes as C
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
import shutil
import struct
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE/'l2_fast'))
import l2_fast
import benchmark

PROOFS = ROOT.parent/'proofs/claude-product-standard-phase0-v1-20261102/team-search-v1'
FLOOR = int(20.5*1024**3)
ISOLATION = 'process isolation confirmed by reviewer at 11:45 and no other jobs scheduled'
ACTIVE = set()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False)
        f.write('\n')


def append(path, value):
    with path.open('a') as f:
        f.write(json.dumps(value)+'\n')


def observation():
    raw = subprocess.check_output(['uptime'], text=True).strip()
    loads = [float(v) for v in re.search(r'load averages?:\s*(.*)', raw)[1].replace(',', ' ').split()]
    return dict(time=time.time(), uptime=raw, loads=loads,
                free_bytes=shutil.disk_usage(ROOT).free, process_isolation=ISOLATION)


def gate(out):
    start = time.monotonic()
    while True:
        o = observation()
        append(out/'load-gates.jsonl', o)
        if o['free_bytes'] < FLOOR:
            raise RuntimeError('20.5 GiB storage floor')
        if o['loads'][0] <= 2.0:
            return o
        if time.monotonic()-start > 300:
            raise RuntimeError('idle gate did not clear in five minutes; resume later')
        print('waiting for load', o['loads'], flush=True)
        time.sleep(20)


def monitor(out, stop):
    while not stop.is_set():
        free = shutil.disk_usage(ROOT).free
        append(out/'storage.jsonl', dict(time=time.time(), free_bytes=free))
        if free < FLOOR:
            for process in tuple(ACTIVE):
                process.terminate()
            os._exit(3)
        stop.wait(5)


def node_result(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
    ACTIVE.add(process)
    try:
        raw, _ = process.communicate()
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, command, raw)
        return json.loads(raw)
    finally:
        ACTIVE.discard(process)


def snapshot(out, rev, wasm=False):
    d = out/rev
    d.mkdir(exist_ok=True)
    for name in ('l2.cpp', 'l2.h', 'cli.cpp'):
        p = d/name
        if not p.exists():
            p.write_bytes(subprocess.check_output(['git', 'show', f'{rev}:research/team-search/l2_fast/{name}'], cwd=ROOT))
    if wasm:
        sys.path.insert(0, str(ROOT/'app'))
        from portable_wasm import toolchain, FLAGS
        compiler, env = toolchain(ROOT)
        flags = [*FLAGS, '-sEXPORTED_FUNCTIONS=["_l2_create","_l2_destroy","_l2_score_many","_alloc","_release","_l2_generate","_l2_enumerate"]']
        target = d/'l2.wasm'
        if not target.exists():
            subprocess.run([str(compiler), *flags, str(d/'l2.cpp'), '-o', str(target)], env=env, check=True)
    else:
        target = d/'libl2.dylib'
        flags = l2_fast.FLAGS
        if not target.exists():
            subprocess.run(['clang++', *flags, str(d/'l2.cpp'), '-shared', '-fPIC', '-o', str(target)], check=True)
            subprocess.run(['clang++', *flags, str(d/'l2.cpp'), str(d/'cli.cpp'), '-o', str(d/'l2-cli')], check=True)
    return target


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--phase', choices=('baseline', 'after'), required=True)
    p.add_argument('--only', choices=('score', 'enumerate', 'wasm-enumerate'))
    a = p.parse_args(); out = a.out; out.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-B', str(ROOT/'scripts/nikke_storage.py'),
               'storage-check', '--required-bytes', str(300*1024**2),
               '--reserve-bytes', str(FLOOR)]
    preflight = subprocess.run(command, capture_output=True, text=True)
    append(out/'storage-preflights.jsonl', dict(time=time.time(), command=command,
           exit=preflight.returncode, stdout=preflight.stdout, stderr=preflight.stderr))
    if preflight.returncode:
        raise RuntimeError('storage preflight failed; see storage-preflights.jsonl')
    stop = threading.Event()
    threading.Thread(target=monitor, args=(out, stop), daemon=True).start()
    try:
        run(a, out)
    finally:
        stop.set()


def run(a, out):
    paths = dict(v1=PROOFS/'s18/profiles.json', v2=PROOFS/'s20/dev/final-profiles.json', v3=PROOFS/'s22/final-profiles.json')
    if a.phase == 'baseline':
        configs = [('s21', 'v2', snapshot(out, '556d63b7'), None)]
        head = snapshot(out, '41ccb6d9')
        # Always use the historical source, including when this coordinator is
        # rerun after the checkout's scorer has already been optimized.
        wasm = snapshot(out, '41ccb6d9', True)
        configs += [('head', v, head, wasm) for v in paths]
    else:
        lib = l2_fast.build(); wasm = l2_fast.build(True)
        configs = [('after', v, lib, wasm) for v in paths]
    done = {json.loads(l)['job'] for l in (out/'runs.jsonl').read_text().splitlines()} if (out/'runs.jsonl').exists() else set()
    s9 = [r['members'] for r in map(json.loads, (HERE/'s9-dataset.jsonl').read_text().splitlines()) if r['backend']=='native_detail' and r.get('total_damage', 0)>0]
    for tag, version, lib, wasm in configs:
        score = l2_fast.Score.load(paths[version], library=lib)
        table = out/f'{tag}-{version}.l2ft'
        if not table.exists(): table.write_bytes(score.raw)
        score.lib.l2_generate.argtypes = [C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32), C.c_size_t, C.c_int]
        score.lib.l2_generate.restype = C.c_uint32
        roster = random.Random(190150).sample(score.names, 150)
        family = [roster[:3]+list(pair) for pair in itertools.permutations(roster[3:], 2)]
        if a.only in (None, 'score'):
            for engine in (['native', 'WASM'] if wasm else ['native']):
                for workload, rows, count in [('S9', s9, len(s9)), ('random', None, 10000000), ('family', family, len(family))]:
                    input_file = out/(workload+'.u32')
                    if rows and not input_file.exists(): input_file.write_bytes(bytes(score._indices(rows)))
                    for workers in (1, 10):
                        for repeat in range(3):
                            job = f'{tag}-{version}-{engine}-{workload}-{workers}-{repeat}'
                            if job in done: continue
                            before = gate(out)
                            if engine == 'native': r = benchmark.native(score, count, workers, rows)
                            else:
                                cmd = ['node', str(HERE/'l2_fast/runner.mjs'), '--bench', '--wasm', str(wasm), '--table', str(table), '--workers', str(workers), '--count', str(count)]
                                if rows: cmd += ['--input', str(input_file)]
                                r = node_result(cmd)
                            after = observation()
                            record = dict(job=job, tag=tag, version=version, engine=engine, workload=workload, repeat=repeat, before=before, after=after, library=str(lib), library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(), **r)
                            append(out/'runs.jsonl', record)
                            print(job, r['kernel_ns_per_squad'], 'load', before['loads'][0], after['loads'][0], flush=True)
        if version != 'v1' and a.only in (None, 'enumerate', 'wasm-enumerate'):
            sizes = (150,) if a.phase == 'baseline' else (150, 206)
            for n in sizes:
                if a.only == 'wasm-enumerate' and not wasm: continue
                engines = ['WASM'] if a.only == 'wasm-enumerate' else ['native']
                for engine in engines:
                    job = f'{tag}-{version}-{engine}-enumerate-{n}'
                    if job in done: continue
                    roster_path = PROOFS/f's21/roster-{n}.json'
                    before = gate(out); start = time.perf_counter()
                    if engine == 'native': r = l2_fast.enumerate_top(score, json.loads(roster_path.read_text()), 10000, 10, 1)
                    else:
                        r = node_result(['node', str(HERE/'l2_fast/runner.mjs'), '--enumerate', '--wasm', str(wasm), '--table', str(table), '--roster', str(roster_path), '--workers', '10', '--stride', '100'])
                    wall = time.perf_counter()-start
                    after = observation(); save(out/(job+'.json'), r)
                    record = dict(job=job, tag=tag, version=version, engine=engine, workload='enumerate', n=n, workers=10, stride=100 if engine=='WASM' else 1, wall_seconds=wall, counts=r['counts'], before=before, after=after)
                    append(out/'runs.jsonl', record); print(job, wall, 'load', before['loads'][0], after['loads'][0], flush=True)
                    if engine == 'native' and a.phase == 'after':
                        reference_path = (PROOFS/f's21/native-{n}-15-10-1.json' if version == 'v2'
                                          else PROOFS/f's22/search-cap/v3-{n}.json')
                        reference = json.loads(reference_path.read_text())
                        assert len(r['entries']) == len(reference['entries']) == 10000
                        assert all(x['indices'] == y['indices'] and
                                   struct.pack('<d', x['score']) == struct.pack('<d', y['score'])
                                   for x, y in zip(r['entries'], reference['entries']))
                        assert all(r['counts'][key] == reference['counts'][key]
                                   for key in ('visited', 'covered', 'scored'))
                        save(out/(job+'-identity.json'), dict(reference=str(reference_path),
                             entries=10000, differences=0, counts_identical=True))
        score.close()


if __name__ == '__main__':
    main()
