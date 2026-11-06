"""S17 resumable CPU-only experiment runner. Run on Mac or gx10.

prepare writes S1 bodies and stratified sample; run uses fresh Python children,
20-worker gx10 pool, monitored reserve and a bounded evidence budget. No deletion.
"""
import argparse, concurrent.futures, copy, json, math, os, pathlib, shutil
import socket, subprocess, sys, threading, time
sys.dont_write_bytecode = True
import bucket_log as b
RESERVE = int(20.5*1024**3)
BUDGET = 200*1024**2


def save(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def prepare(out):
    i=json.loads((b.ROOT/'research/team-search/s1-inputs.json').read_text())
    body=json.loads(pathlib.Path(i['benchmark']).read_text())[0];body.update(i['settings'])
    body['compute_backend']='cpu'
    rows=[json.loads(l) for l in (b.ROOT/'research/team-search/s9-dataset.jsonl').read_text().splitlines()]
    rows=sorted((r for r in rows if (r.get('total_damage') or 0)>0 and r['backend']=='native_detail'),key=lambda r:(r['total_damage'],r['id']))
    # Two ordered squads per damage decile: midpoint and upper boundary.
    selected=[]
    for decile in range(10):
        for fraction in (.5, 1.):
            rank=min(len(rows)-1,math.ceil((decile+fraction)*len(rows)/10)-1)
            row=rows[rank];v=copy.deepcopy(body);v['squad']=row['members']
            # A complete S1 profile is preserved in the shared body. No growth changes.
            selected.append(dict(id=row['id'],decile=decile+1,rank=rank+1,
                                 native_damage=row['total_damage'],members=row['members']))
    save(out/'body.json',body);save(out/'selection.json',dict(population=len(rows),selected=selected))


def evaluate(body, logged):
    r=subprocess.run([sys.executable,str(b.ROOT/'research/team-search/bucket_log.py'),'--worker'],
                     input=json.dumps(dict(body=body,logged=logged)),text=True,capture_output=True,
                     env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=900)
    if r.returncode:raise RuntimeError(r.stderr[-12000:]+r.stdout[-1000:])
    return json.loads(r.stdout)


def one(row,out):
    target=out/(str(row['id'])+'.json')
    if target.exists():
        existing=json.loads(target.read_text())
        if existing['selection']!=row:raise ValueError('Resume selection mismatch')
        return existing
    started=time.perf_counter();body=json.loads((out/'body.json').read_text());body['squad']=row['members']
    baseline=evaluate(body,False);logged=evaluate(body,True)
    if b.clean(baseline['payload'])!=b.clean(logged['payload']):raise AssertionError('Non-interference')
    result=dict(selection=row,host=socket.gethostname(),baseline=baseline,logged=logged,non_interference=True,variants=[])
    for knob,(group,magnitudes) in b.KNOBS.items():
        for magnitude in magnitudes:
            if shutil.disk_usage(out).free<RESERVE:raise RuntimeError('Storage reserve')
            actual=evaluate(b.perturb(body,knob,magnitude),False)
            prediction=logged['buckets']['unit_predictions'][knob][str(magnitude)]
            change=actual['payload']['total_damage']-baseline['payload']['total_damage']
            result['variants'].append(dict(knob=knob,group=group,magnitude=magnitude,actual_change=change,
                 predicted_change=prediction,seconds=actual['seconds'],payload_digest=actual['payload_digest'],
                 total_damage=actual['payload']['total_damage'],
                 hit_count_changes={k:actual['diagnostic']['hit_counts'].get(k,0)-baseline['diagnostic']['hit_counts'].get(k,0)
                    for k in actual['diagnostic']['hit_counts'].keys()|baseline['diagnostic']['hit_counts'].keys()
                    if actual['diagnostic']['hit_counts'].get(k,0)!=baseline['diagnostic']['hit_counts'].get(k,0)},
                 diagnostic=actual['diagnostic'],base_stats=actual['payload']['base_stats'],
                 burst_timeline_changed=actual['payload']['burst_timeline']!=baseline['payload']['burst_timeline']))
    result['wall_seconds']=time.perf_counter()-started
    save(target,result)
    return result


def run(out,workers):
    initial=shutil.disk_usage(out).free
    if initial<RESERVE+BUDGET:raise RuntimeError('Need 20.5 GiB reserve plus 200 MiB budget')
    selection=json.loads((out/'selection.json').read_text())['selected']
    storage=[];stop=threading.Event();started=time.perf_counter()
    def monitor():
        while not stop.is_set():
            free=shutil.disk_usage(out).free
            storage.append(dict(time=time.time(),free_bytes=free))
            save(out/'storage.json',dict(initial_free=initial,min_free=min(r['free_bytes'] for r in storage),samples=storage))
            if free<RESERVE:os._exit(3)
            stop.wait(10)
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            tasks={pool.submit(one,row,out):row['id'] for row in selection}
            for f in concurrent.futures.as_completed(tasks):
                r=f.result();print(json.dumps(dict(id=tasks[f],seconds=r['wall_seconds'],damage=r['baseline']['payload']['total_damage'])),flush=True)
        save(out/'run.json',dict(host=socket.gethostname(),workers=workers,wall_seconds=time.perf_counter()-started,squads=len(selection)))
    finally:stop.set();thread.join()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run']);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--workers',type=int,default=20)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if a.action=='prepare':prepare(a.out)
    else:run(a.out,a.workers)
if __name__=='__main__':main()
