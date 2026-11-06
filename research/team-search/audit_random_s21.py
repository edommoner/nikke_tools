"""Ensure S21's random identity evidence covers 100,000 distinct subsets.

Replay only RNG/coverage for the saved sample; verify any shortfall with new
unique subsets through enumeration, binding, CLI, WASM and Python binary64.
"""
import argparse, ctypes as C, hashlib, json, random, struct, subprocess, time
from pathlib import Path
import l2_fast,l2_score_s20
from search_s21 import DEFAULT,HERE,read,save,profiles

def audit(out,mask=15):
    lib=l2_fast.build();wasm=l2_fast.build(True);results=[]
    for n in (150,206):
        started=time.perf_counter();p=profiles(out,mask);score=l2_fast.Score(p,library=lib);oracle=l2_score_s20.Score(p);rng=random.Random(210021+n+mask);roster=read(out/f'roster-{n}.json');seen=set();rejected=0
        def next_covered():
            nonlocal rejected
            while True:
                ids=tuple(sorted(rng.sample(roster,5)))
                if l2_score_s20.cycle([score.names[i] for i in ids],p['characters'],p['settings']['duration'])[2]:return ids
                rejected+=1
        original_rows=100000 if mask==15 else 10000
        for _ in range(original_rows):seen.add(next_covered())
        original_unique=len(seen);original_rejected=rejected
        prior=next(r for r in read(out/'bit-identity.json') if r['n']==n and r['mask']==mask and r['label']=='random')
        assert prior['count']==original_rows and prior['rejected']==original_rejected
        extra=[]
        while len(seen)<100000:
            ids=next_covered()
            if ids not in seen:seen.add(ids);extra.append(ids)
        wire=(C.c_uint32*(len(extra)*5))(*(i for ids in extra for i in ids));native=score.score_indices(wire)
        cli=subprocess.check_output([str(lib.parent/'l2-cli'),str(out/f'mask-{mask}.l2ft')],input=bytes(wire))
        wasm_values=subprocess.check_output(['node',str(HERE/'l2_fast/runner.mjs'),'--wasm',str(wasm),'--table',str(out/f'mask-{mask}.l2ft')],input=bytes(wire))
        fn=score.lib.l2_enumerate;fn.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_size_t,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(l2_fast.Entry),C.POINTER(C.c_size_t),C.POINTER(l2_fast.Counts)];fn.restype=C.c_int
        digest=hashlib.sha256()
        for j,ids in enumerate(extra):
            one=(C.c_uint32*5)(*ids);entry=l2_fast.Entry();count=C.c_size_t();counts=l2_fast.Counts()
            assert fn(score.table,one,5,1,0,1,1,C.byref(entry),C.byref(count),C.byref(counts))==0 and count.value==1
            expected=struct.pack('<d',oracle([score.names[i] for i in ids]))
            assert list(entry.ids)==list(ids)
            assert all(v==expected for v in [struct.pack('<d',entry.score),struct.pack('<d',native[j]),cli[j*48:j*48+8],wasm_values[j*48:j*48+8]])
            digest.update(expected)
        results.append(dict(n=n,mask=mask,original_rows=original_rows,original_unique=original_unique,extra_verified=len(extra),final_unique=len(seen),differences=0,sha256_extra=digest.hexdigest(),seconds=time.perf_counter()-started))
        score.close();save(out/('random-unique-audit.json' if mask==15 else 'random-unique-audit-mask2.json'),results);print(results[-1],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=DEFAULT/'s21');p.add_argument('--mask',type=int,choices=[15,2],default=15);a=p.parse_args();audit(a.out,a.mask)
