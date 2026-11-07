"""S26 isolated local scalar timings; no detailed execution."""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import bench_s23 as b
import l2_fast
import truth_s26 as truth


def run(out, profiles, label, rosters, wasm_score=False):
    if (out.parent/'PAUSE_TIMINGS').exists():raise RuntimeError('Timing coordinator paused for a recorded implementation change')
    out.mkdir(exist_ok=True)
    b.ISOLATION = 'S26 coordinator runs no other local scoring/tests during timings; host background activity unverified'
    cmd = ['python3.12','-B','scripts/nikke_storage.py','storage-check',
           '--required-bytes','150000000','--reserve-bytes',str(b.FLOOR)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    b.append(out/'preflights.jsonl',dict(command=cmd,exit=p.returncode,stdout=p.stdout))
    if p.returncode:raise RuntimeError('storage preflight')
    lib = l2_fast.build()
    identity = dict(profiles_sha256=truth.old.digest(profiles), library=str(lib),
                    library_sha256=truth.old.digest(lib),
                    table_sha256=hashlib.sha256(l2_fast.compile_profiles(json.loads(profiles.read_text()))).hexdigest())
    receipt = out/(label+'-build.json')
    if receipt.exists():assert json.loads(receipt.read_text())==identity
    else:b.save(receipt, identity)
    s = l2_fast.Score.load(profiles, library=lib)
    s.lib.l2_generate.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32),C.c_size_t,C.c_int]
    s.lib.l2_generate.restype=C.c_uint32
    for rep in range(3):
        path=out/f'{label}-score-{rep}.json'
        if path.exists():continue
        before=b.gate(out);r=b.benchmark.native(s,10000000,1,None);after=b.observation()
        b.save(path,dict(before=before,after=after,**r));print(label,rep,r['kernel_ns_per_squad'],flush=True)
    for n in rosters:
        path=out/f'{label}-enumerate-{n}.json'
        if path.exists():continue
        roster=json.loads((truth.DEFAULT.parent/f's21/roster-{n}.json').read_text())
        before=b.gate(out);start=time.perf_counter()
        r=l2_fast.enumerate_top(s,roster,10000,10,1)
        wall=time.perf_counter()-start;after=b.observation()
        b.save(path,dict(before=before,after=after,wall_seconds=wall,**r))
        if label.startswith('v3'):
            ref=json.loads((truth.DEFAULT.parent/f's22/search-cap/v3-{n}.json').read_text())
            assert len(r['entries'])==len(ref['entries'])==10000
            assert all(a['indices']==c['indices'] and b.struct.pack('<d',a['score'])==b.struct.pack('<d',c['score']) for a,c in zip(r['entries'],ref['entries']))
            assert all(r['counts'][k]==ref['counts'][k] for k in ('visited','covered','scored'))
            b.save(out/f'{label}-identity-{n}.json',dict(differences=0,entries=10000,counts_identical=True))
        print(label,n,wall,flush=True)
    s.close()
    if wasm_score:
        wasm=l2_fast.build(True)
        table=out/(label+'.l2ft')
        if not table.exists():table.write_bytes(l2_fast.compile_profiles(json.loads(profiles.read_text())))
        for rep in range(3):
            path=out/f'{label}-wasm-score-{rep}.json'
            if path.exists():continue
            before=b.gate(out)
            r=b.node_result(['node',str(b.HERE/'l2_fast/runner.mjs'),'--bench','--wasm',str(wasm),
                '--table',str(table),'--workers','1','--count','10000000'])
            after=b.observation()
            b.save(path,dict(before=before,after=after,wasm=str(wasm),wasm_sha256=truth.old.digest(wasm),**r))
            print(label,'WASM',rep,r['kernel_ns_per_squad'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=truth.DEFAULT/'timings')
    p.add_argument('--profiles',type=Path,default=truth.DEFAULT.parent/'s22/final-profiles.json')
    p.add_argument('--label',default='v3-before')
    p.add_argument('--rosters',type=int,nargs='*',choices=(150,206),default=[150,206])
    p.add_argument('--wasm-score',action='store_true')
    a=p.parse_args()
    stop=threading.Event()
    a.out.mkdir(exist_ok=True)
    threading.Thread(target=b.monitor,args=(a.out,stop),daemon=True).start()
    try:run(a.out,a.profiles,a.label,a.rosters,a.wasm_score)
    finally:stop.set()
