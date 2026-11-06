"""Bounded streaming Mac benchmark; every measured run is retained as JSONL.

No output corpus is stored. Kernels include validation, cycle, recipient selection,
all bucket arithmetic and dependencies. Generation, binding packing and checksums
are outside kernel timers; end-to-end wall times are also retained.
"""
import argparse, concurrent.futures, ctypes as C, itertools, json, math, pathlib, random, statistics, subprocess, sys, time, threading
HERE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
import l2_fast,l2_score

def native(score,count,workers,input_rows):
    counts=[count//workers+(i<count%workers) for i in range(workers)]
    if len({(n+8191)//8192 for n in counts})!=1:raise ValueError('workers must have equal batch counts')
    barrier=threading.Barrier(workers)
    def worker(i):
        n=count//workers+(i<count%workers);first=i*(count//workers)+min(i,count%workers);seed=190019+i;batch=8192;ids=(C.c_uint32*(batch*5))();out=(C.c_double*batch)();seconds=0.;checksum=0.;batch_seconds=[]
        src=score._indices(input_rows) if input_rows else None
        for offset in range(0,n,batch):
            size=min(batch,n-offset)
            if src:
                # Match the Node worker's repeated row stream.
                for row in range(size):C.memmove(C.byref(ids,row*20),C.byref(src,((first+offset+row)%len(input_rows))*20),20)
            else:seed=score.lib.l2_generate(score.table,seed,ids,size,1)
            barrier.wait()
            start=time.perf_counter_ns();rc=score.lib.l2_score_many(score.table,ids,size,out,None);elapsed=(time.perf_counter_ns()-start)/1e9;seconds+=elapsed;batch_seconds.append(elapsed)
            barrier.wait()
            if rc:raise RuntimeError('score error')
            checksum+=sum(out[:size])
        return dict(seconds=seconds,checksum=checksum,seed=seed,batch_seconds=batch_seconds)
    start=time.perf_counter()
    if workers==1:results=[worker(0)]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:results=list(pool.map(worker,range(workers)))
    return dict(workers=workers,count=count,wall_seconds=time.perf_counter()-start,kernel_seconds=[r['seconds'] for r in results],kernel_ns_per_squad=sum(max(column) for column in zip(*(r['batch_seconds'] for r in results)))*1e9/count,results=results)

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--profiles',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True);a.add_argument('--count',type=int,default=10000000);a.add_argument('--repeats',type=int,default=3);args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    lib=l2_fast.build();wasm=l2_fast.build(True);score=l2_fast.Score.load(args.profiles,library=lib);table=args.out/'profiles.l2ft';table.write_bytes(score.raw)
    score.lib.l2_generate.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32),C.c_size_t,C.c_int];score.lib.l2_generate.restype=C.c_uint32
    rows=[json.loads(l) for l in (HERE.parent/'s9-dataset.jsonl').read_text().splitlines()];s9=[r['members'] for r in rows if r['backend']=='native_detail' and r.get('total_damage',0)>0]
    roster=random.Random(190150).sample(score.names,150);prefix=roster[:3];family=[prefix+list(pair) for pair in itertools.permutations(roster[3:],2)]
    (args.out/'workload.json').write_text(json.dumps(dict(random_seed=190019,generator='xorshift32 modulo 206; distinct member rejection; reject cycle stage union != 7',random_count=args.count,roster_seed=190150,roster=roster,prefix=prefix,family_count=len(family),family_policy='fixed first three; both orders of distinct last two from remaining 147'),ensure_ascii=False,indent=2)+'\n')
    inputs={}
    for label,squads in [('S9',s9),('family',family)]:
        file=args.out/(label+'.u32');file.write_bytes(bytes(score._indices(squads)));inputs[label]=file
    receipt=args.out/'benchmark.jsonl'
    def record(x):
        x['recorded_at']=time.time()
        with receipt.open('a') as f:f.write(json.dumps(x)+'\n')
        print(json.dumps(x),flush=True)
    import l2_score_s20
    oracle=(l2_score_s20.Score if 's20' in score.profiles else l2_score.Score)(score.profiles)
    for repeat in range(args.repeats):
        checksum=0.;start=time.perf_counter_ns()
        for squad in s9[:512]:checksum+=oracle(squad)
        record(dict(engine='Python oracle',workload='S9 first512',repeat=repeat,count=512,workers=1,kernel_ns_per_squad=(time.perf_counter_ns()-start)/512,checksum=checksum))
    for label,count,squads in [('S9',len(s9),s9),('random',args.count,None),('family',len(family),family)]:
        for workers in (1,10):
            for repeat in range(args.repeats):record(dict(engine='native',workload=label,repeat=repeat,**native(score,count,workers,squads)))
    for label,count in [('S9',len(s9)),('random',args.count),('family',len(family))]:
        for workers in (1,10):
            for repeat in range(args.repeats):
                cmd=['node',str(HERE/'runner.mjs'),'--bench','--wasm',str(wasm),'--table',str(table),'--workers',str(workers),'--count',str(count)]
                if label in inputs:cmd+=['--input',str(inputs[label])]
                r=json.loads(subprocess.check_output(cmd,text=True));record(dict(engine='WASM',workload=label,repeat=repeat,**r))
if __name__=='__main__':main()
