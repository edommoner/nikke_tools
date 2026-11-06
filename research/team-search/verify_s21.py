"""Independent binary64 acceptance and full-list determinism for S21.

Random visited subsets are uniform distinct subsets, in canonical order,
rejected only by the oracle's cycle coverage. No random corpus is stored.
"""
import argparse, ctypes as C, hashlib, json, os, random, struct, subprocess, time
from pathlib import Path
import l2_fast, l2_score_s20
from search_s21 import read, save, profiles, DEFAULT


def verify(out,random_count):
    lib=l2_fast.build();wasm=l2_fast.build(True);receipt=[]
    rosters=read(out/'rosters.json')['rosters']
    for n in (150,206):
        for mask in (15,2):
            p=profiles(out,mask);score=l2_fast.Score(p,library=lib);oracle=l2_score_s20.Score(p)
            enum=score.lib.l2_enumerate;enum.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_size_t,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(l2_fast.Entry),C.POINTER(C.c_size_t),C.POINTER(l2_fast.Counts)];enum.restype=C.c_int
            entry=l2_fast.Entry();entry_count=C.c_size_t();counts=l2_fast.Counts()
            entries=read(out/f'native-{n}-{mask}-10-1.json')['entries']
            for label in ('retained','random'):
                start=time.perf_counter();rng=random.Random(210021+n+mask);digest=hashlib.sha256();count=0;rejected=0
                target=len(entries) if label=='retained' else (random_count if mask==15 else 10000)
                while count<target:
                    indices=[]
                    for i in range(min(2048,target-count)):
                        if label=='retained':ids=entries[count+i]['indices']
                        else:
                            while True:
                                ids=sorted(rng.sample(rosters[str(n)],5));squad=[score.names[j] for j in ids]
                                if l2_score_s20.cycle(squad,p['characters'],p['settings']['duration'])[2]:break
                                rejected+=1
                        indices.append(ids)
                    squads=[[score.names[i] for i in ids] for ids in indices]
                    ids=(C.c_uint32*(len(indices)*5))(*(i for row in indices for i in row))
                    native=score.score_indices(ids)
                    cli=subprocess.check_output([str(lib.parent/'l2-cli'),str(out/f'mask-{mask}.l2ft')],input=bytes(ids))
                    w=subprocess.check_output(['node',str(Path(__file__).parent/'l2_fast/runner.mjs'),'--wasm',str(wasm),'--table',str(out/f'mask-{mask}.l2ft')],input=bytes(ids))
                    for i,squad in enumerate(squads):
                        expected=struct.pack('<d',oracle(squad));actual=struct.pack('<d',native[i])
                        values=[actual,cli[i*48:i*48+8],w[i*48:i*48+8]]
                        # Re-enter the actual enumeration primitive on this
                        # visited five-member subset, not only score_many.
                        one=(C.c_uint32*5)(*indices[i])
                        rc=enum(score.table,one,5,1,0,1,1,C.byref(entry),C.byref(entry_count),C.byref(counts))
                        assert rc==0 and entry_count.value==1 and counts.visited==counts.covered==counts.scored==1
                        assert list(entry.ids)==indices[i]
                        values.append(struct.pack('<d',entry.score))
                        if label=='retained':values.append(struct.pack('<d',entries[count+i]['score']))
                        if any(v!=expected for v in values):raise AssertionError(dict(n=n,mask=mask,label=label,row=count+i,squad=squad,expected=expected.hex(),actual=[v.hex() for v in values]))
                        digest.update(expected)
                    count+=len(squads)
                r=dict(n=n,mask=mask,label=label,count=count,rejected=rejected,differences=0,sha256=digest.hexdigest(),seconds=time.perf_counter()-start,engines=['enumerator','binding','CLI','WASM','Python3.12 oracle'])
                receipt.append(r);save(out/'bit-identity.json',receipt);print(r,flush=True)
            score.close()


def determinism(out):
    results=[]
    # Compare identical sampled domains for all engines / counts, rather than
    # treating a fraction's top-K as if it were the exhaustive top-K.
    for n in (150,206):
        for mask in (15,2):
            p=profiles(out,mask);score=l2_fast.Score(p)
            target=out/f'native-{n}-{mask}-10-100.json'
            if not target.exists():
                result=l2_fast.enumerate_top(score,read(out/f'roster-{n}.json'),10000,10,100);save(target,dict(result,engine='native',n=n,mask=mask,workers=10,stride=100,wall_seconds=result['counts']['seconds']))
            score.close()
            files=[out/f'{engine}-{n}-{mask}-{workers}-100.json' for engine in ('native','WASM') for workers in (1,10)]
            rows=[read(p) for p in files];base=rows[0]['entries']
            for r in rows:
                assert r['entries']==base,(n,mask,r['engine'],r['workers'])
                assert {k:r['counts'][k] for k in ('visited','covered','scored')}=={k:rows[0]['counts'][k] for k in ('visited','covered','scored')}
            results.append(dict(n=n,mask=mask,stride=100,entries=len(base),engines=['native1','native10','WASM1','WASM10'],identical=True))
    save(out/'determinism.json',results)

def full_determinism(out):
    results=[];lib=l2_fast.build();wasm=l2_fast.build(True)
    for n in (150,206):
        base=read(out/f'native-{n}-15-10-1.json')
        for engine,workers in [('native',7),('WASM',10)]:
            target=out/f'{engine}-{n}-15-{workers}-1.json'
            if not target.exists():
                start=time.perf_counter()
                if engine=='native':
                    score=l2_fast.Score(profiles(out,15),library=lib);r=l2_fast.enumerate_top(score,read(out/f'roster-{n}.json'),10000,workers,1);score.close()
                else:
                    r=json.loads(subprocess.check_output(['node',str(Path(__file__).parent/'l2_fast/runner.mjs'),'--enumerate','--wasm',str(wasm),'--table',str(out/'mask-15.l2ft'),'--roster',str(out/f'roster-{n}.json'),'--k','10000','--workers',str(workers)],text=True))
                r.update(engine=engine,n=n,mask=15,workers=workers,stride=1,wall_seconds=time.perf_counter()-start,concurrent_validation=bool(os.environ.get('S21_CONCURRENT_VALIDATION')));save(target,r)
            r=read(target);assert r['entries']==base['entries'],(n,engine,workers)
            assert all(r['counts'][k]==base['counts'][k] for k in ('visited','covered','scored'))
            results.append(dict(n=n,engine=engine,workers=workers,entries=len(r['entries']),counts=r['counts'],identical=True,wall_seconds=r['wall_seconds']))
            save(out/'full-determinism.json',results);print(results[-1],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['verify','determinism','full-determinism']);p.add_argument('--out',type=Path,default=DEFAULT/'s21');p.add_argument('--random',type=int,default=100000);a=p.parse_args()
    if a.action=='verify':verify(a.out,a.random)
    elif a.action=='determinism':determinism(a.out)
    else:full_determinism(a.out)
