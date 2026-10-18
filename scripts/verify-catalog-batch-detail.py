"""Current accepted catalog: independent whole battles, with GPU batch execution.

Each GPU input is an owned profile, effects and a common authored frame schedule.
CPU event histories and simulation states are never replayed into the kernel.
"""
import argparse,copy,hashlib,json,random,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for,coverage
import detail_gpu
from gpu_selector import Cuda

def evaluate_batch(device,items,backend):
    outputs=detail_gpu.evaluate_full_many(device,[item[2] for item in items],module_backend=backend)
    assert len(outputs)==len(items)
    rows=[]
    for (name,body,compiled),gpu in zip(items,outputs):
        cpu=a.evaluate(body);rng=list(random.getstate()[1])
        checks={k:cpu[k]==gpu[k] for k in ('total_damage','members','base_stats','burst_timeline','burst_gauge_mode','shooting_policy','weapon_mode_swap','seed')}
        checks['final_random_state']=rng==gpu['_random_state']
        row=dict(character=name,backend=backend,passed=all(checks.values()),checks=checks,
                 cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],batch_size=len(items),
                 batch_elapsed_ms=gpu['compute']['elapsed_ms'],workspace_bytes=gpu['compute']['workspace_bytes'],weapon_mode_swap=gpu['weapon_mode_swap'],gpu_group_size=gpu['compute']['batch_size'])
        if not row['passed']:row.update(cpu_members=cpu['members'],gpu_members=gpu['members'],cpu_bursts=cpu['burst_timeline'],gpu_bursts=gpu['burst_timeline'])
        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    return rows

def main(args):
    audit=coverage();prepared=[];rows=[];nameset=[]
    for entry in audit['results']:
        if not entry['supported']:continue
        name=entry['character']
        if args.character and name!=args.character:continue
        if args.limit and len(nameset)>=args.limit:break
        names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4]
        body=body_for(names,args.duration,True)
        body.update(seed=args.seed,shooting_policy=args.shooting_policy,burst_policy='rules',
                    burst_gauge_mode=args.mode,_debug_random_state=True)
        nameset.append(name)
        try:prepared.append((name,body,a.evaluate({**body,'_compile_gpu_detail':True})))
        except Exception as error:rows.append(dict(character=name,backend='compile',passed=False,error=str(error)))
    device=Cuda();fatal_error=None
    backends=('native','ptx') if args.backend=='both' else (args.backend,)
    try:
        for backend in backends:
            for start in range(0,len(prepared),args.batch_size):
                batch=prepared[start:start+args.batch_size]
                try:rows.extend(evaluate_batch(device,batch,backend))
                except Exception as error:
                    # A failed batch is never accepted as a partially valid GPU
                    # result. Preserve every failed member for a focused repro.
                    for name,body,compiled in batch:
                        row=dict(character=name,backend=backend,passed=False,status='unverified_batch_error',error=str(error),batch_size=len(batch))
                        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
                    if 'CUDA' in str(error):
                        # A CUDA execution fault poisons its context. Later
                        # launches cannot establish character-level parity.
                        fatal_error=str(error);break
            if fatal_error:break
    finally:device.close()
    files=['scripts/verify-catalog-batch-detail.py','scripts/detail_coverage.py','app/detail_gpu.py','app/detail_effects.cu',
           'app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
    return dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(rows) and all(r['passed'] for r in rows),
        objective_complete=False,catalog_characters=audit['characters'],compiled_characters=audit['supported'],
        selected_characters=nameset,settings=dict(duration=args.duration,mode=args.mode,shooting_policy=args.shooting_policy,seed=args.seed),
        cases=rows,rejected_characters=[r for r in audit['results'] if not r['supported']],
        fatal_cuda_error=fatal_error,not_executed=[dict(character=n,backend=b) for b in backends for n in nameset if not any(row['character']==n and row['backend']==b for row in rows)],
        cpu_trace_used_as_gpu_input=False,gpu_batch_execution=True,
        scope='Current accepted characters, one grown favorite-zero/no-cube five-member squad each, selected settings, raw source skills. Not every favorite or combination.',
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx','both'],default='both');p.add_argument('--batch-size',type=int,default=8)
    p.add_argument('--duration',type=int,default=30);p.add_argument('--seed',type=int,default=12345);p.add_argument('--mode',choices=['fixed','accumulate'],default='fixed')
    p.add_argument('--shooting-policy',choices=['auto','character'],default='auto');p.add_argument('--character');p.add_argument('--limit',type=int);p.add_argument('--output',default='research/detail-catalog-batch-verification.json');args=p.parse_args()
    if not 1<=args.batch_size<=32 or not 1<=args.duration<=180:p.error('batch size 1..32 and duration 1..180 required')
    report=main(args);(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
