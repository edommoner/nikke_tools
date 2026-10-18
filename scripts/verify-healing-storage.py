"""Independent squad and per-name resident buffer snapshots for staged v40."""
import argparse,ast,hashlib,importlib.util,inspect,json,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('storage_definitions','scripts/healing-storage-fixtures.py');g=d.g;v=d.v

def compare(device,name,b,extra,backend):
    b={**b,'_debug_storage_frames':True};frames=[];captured={};keys=[];labels={}
    code=v.s.timeline.simulate.__code__;lines,first=inspect.getsourcelines(v.s.timeline.simulate);tree=ast.parse(textwrap.dedent(''.join(lines)))
    steps=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT'];assert len(steps)==1;end=first+steps[0].lineno-1
    original_eval=g.evaluate_full;original_settrace=sys.settrace;previous=sys.gettrace()
    def evaluate(device,compiled,*args,**kwargs):
        nonlocal keys,labels
        keys=[-1]+sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2]==74});labels={idx:label for label,idx in compiled['program']['states'].items()}
        result=original_eval(device,compiled,*args,**kwargs);captured.update(result);return result
    def settrace(fn):
        if fn is None or fn is previous:return original_settrace(fn)
        def combined(frame,event,arg):
            onward=fn(frame,event,arg)
            if frame.f_code is code and event=='line' and frame.f_lineno==end:
                bm=frame.f_locals['bm'];t=frame.f_locals['t']
                for key in keys:
                    active=[a for a in bm._active if a.effect.get('stat')=='heal_overcharge_store' and (key<0 or a.effect.get('name','')==labels[key])]
                    frames.append(dict(time=t,key=key,current={n:sum(getattr(a,'heal_store_current',{}).get(n,0) for a in active) for n in b['squad']},capacity={n:sum(getattr(a,'heal_store_capacity',{}).get(n,0) for a in active) for n in b['squad']},carriers=len(active)))
            return combined if onward is not None else None
        return original_settrace(combined)
    try:
        with patch.object(g,'evaluate_full',evaluate),patch.object(sys,'settrace',settrace):row=v.compare(device,name,b,extra,backend)
    finally:original_settrace(previous)
    row['checks']['per_name_storage_snapshots']=v.s.v.close(captured.get('_storage_frames'),frames)
    positive=any(any(x>0 for x in f['current'].values()) for f in frames)
    row['checks']['reserve_positive_control']=positive==(name not in ('storage-empty','raw-storage-센티'))
    aggregate=[f for f in frames if f['key']==-1]
    spent=any(a['carriers']==b['carriers'] and a['capacity']==b['capacity'] and any(a['current'][n]>b['current'][n] for n in a['current']) for a,b in zip(aggregate,aggregate[1:]))
    if name in ('storage-damage','storage-drain'):row['checks']['reserve_consumption_exercised']=spent
    if name=='storage-shield-before-storage':row['checks']['outer_shield_prevents_reserve_consumption']=not spent
    row.update(passed=all(row['checks'].values()),storage_frame_rows=len(frames),cpu_model_extended=True,in_game_rules_verified=False)
    if not row['checks']['per_name_storage_snapshots']:row['storage_difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(frames,captured.get('_storage_frames',[]))) if not v.s.v.close(c,x)),dict(cpu_rows=len(frames),gpu_rows=len(captured.get('_storage_frames',[]))))
    print(json.dumps(dict(name=name,passed=row['passed'],failed=[k for k,x in row['checks'].items() if not x])),flush=True);return row

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--real',action='store_true');ap.add_argument('--fail-fast',action='store_true');ap.add_argument('--output',required=True);args=ap.parse_args()
    files=['scripts/verify-healing-storage.py','scripts/healing-storage-fixtures.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']
    files+=['app/'+n for n in (['healing_storage_compat.py','detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['healing_storage_compat.py','detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};planned=[x for x in d.fixtures() if x[0].startswith('raw-')==args.real];rows=[];device=v.s.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:row=compare(device,name,b,extra,args.backend)
            except Exception as e:row=dict(name=name,passed=False,error=repr(e));print(json.dumps(row),flush=True)
            rows.append(row)
            if args.fail_fast and not row['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    result=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),abi=g.DETAIL_ABI,backend=args.backend,stage_only=False,objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,cpu_trace_used_as_gpu_input=False,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes)
    (ROOT/args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if result['passed'] else 1)
