"""Whole-squad and raw resident charge frames, GPU runs before CPU reference."""
import argparse,ast,hashlib,importlib.util,inspect,json,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('charge_definitions','research/heal-charge-fixtures.py');g=d.g;v=d.v
def compare(device,name,b,x,backend):
    b={**b,'_debug_charge_frames':True};frames=[];captured={};keys=[];labels={}
    code=v.s.timeline.simulate.__code__;lines,first=inspect.getsourcelines(v.s.timeline.simulate);tree=ast.parse(textwrap.dedent(''.join(lines)))
    steps=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT'];assert len(steps)==1;end=first+steps[0].lineno-1
    original_eval=g.evaluate_full;original_settrace=sys.settrace;previous=sys.gettrace()
    def evaluate(device,compiled,*args,**kwargs):
        nonlocal keys,labels
        keys=[-1]+sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2]==76});labels={idx:label for label,idx in compiled['program']['states'].items()}
        result=original_eval(device,compiled,*args,**kwargs);captured.update(result);return result
    def settrace(fn):
        if fn is None or fn is previous:return original_settrace(fn)
        def combined(frame,event,arg):
            onward=fn(frame,event,arg)
            if frame.f_code is code and event=='line' and frame.f_lineno==end:
                bm=frame.f_locals['bm'];t=frame.f_locals['t'];active={a.uid for a in bm._active}
                records=list(getattr(bm,'_heal_charge_records',{}).values())
                for key in keys:
                    chosen=[a for a in records if key<0 or a.effect.get('name','')==labels[key]]
                    resident=[a for a in chosen if a.uid in active]
                    amounts={n:sum(a.heal_charge_current for a in chosen if a.caster==n and (a.uid in active or a.heal_charge_ended) and not a.heal_charge_done) for n in b['squad']}
                    capacity={n:sum(a.heal_charge_base_cap for a in resident if a.caster==n) for n in b['squad']}
                    frames.append(dict(time=t,key=key,current=amounts,base_capacity=capacity,carriers=len(resident)))
            return combined if onward is not None else None
        return original_settrace(combined)
    try:
        with patch.object(g,'evaluate_full',evaluate),patch.object(sys,'settrace',settrace):row=v.compare(device,name,b,x,backend)
    finally:original_settrace(previous)
    row['checks']['named_charge_frames']=v.s.v.close(captured.get('_charge_frames'),frames)
    expected_positive=name not in ('charge-empty','raw-charge-taunter-negative')
    row['checks']['positive_charge_control']=any(any(amount>0 for amount in f['current'].values()) for f in frames)==expected_positive
    row['checks']['actual_workspace_bytes']=captured['compute']['workspace_bytes']==1088520
    row.update(passed=all(row['checks'].values()),charge_frame_rows=len(frames),workspace_bytes=captured['compute']['workspace_bytes'],cpu_model_extended=True,in_game_rules_verified=False)
    if not row['checks']['named_charge_frames']:row['charge_difference']=next((dict(index=i,cpu=c,gpu=y) for i,(c,y) in enumerate(zip(frames,captured.get('_charge_frames',[]))) if not v.s.v.close(c,y)),dict(cpu_rows=len(frames),gpu_rows=len(captured.get('_charge_frames',[]))))
    print(json.dumps(dict(name=name,passed=row['passed'],failed=[k for k,y in row['checks'].items() if not y])),flush=True);return row
def fixtures(group):
    if group=='new':return [(SimpleNamespace(compare=compare),*x) for x in [*d.fixtures(),*d.real_fixtures()]]
    old=load('charge_prior_oracles','scripts/verify-heal-sharing.py');cases=old.fixtures('new')+old.fixtures('legacy');assert len(cases)==178;return cases
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--group',choices=['new','legacy'],default='new');ap.add_argument('--output',required=True);ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    planned=fixtures(args.group)
    paths=list((ROOT/'scripts').glob('*.py'))+list((ROOT/'app').glob('*.py'))
    paths += [ROOT/p for p in ['research/verify-heal-charge.py','research/heal-charge-fixtures.py','research/staging/v42/app/heal_charge_compat.py','research/staging/v42/app/detail_gpu.py','research/staging/v42/app/detail_effects.cu','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json','research/upstream/nikke-calc-master/data/parsed_nikke.json','research/upstream/nikke-calc-master/runner/spec.py']]
    paths += [ROOT/'research/staging/v42/app'/n for n in (['detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))}
    output=ROOT/args.output;rows=[]
    if args.resume and output.exists():
        previous=json.loads(output.read_text(encoding='utf-8'));assert previous['source_sha256']==hashes,'Source changed; stale resume rejected';rows=[r for r in previous['cases'] if r['passed']]
    done={r['name'] for r in rows};device=v.s.v.v.v.Cuda()
    def save():
        assert hashes=={p:sha(ROOT/p) for p in hashes}
        r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(r['passed'] for r in rows),abi=g.DETAIL_ABI,backend=args.backend,group=args.group,stage_only=True,objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,cpu_trace_used_as_gpu_input=False,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes)
        output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return r['passed']
    try:
        for oracle,name,b,x in planned:
            if name in done:continue
            try:row=oracle.compare(device,name,b,x,args.backend)
            except Exception as e:row=dict(name=name,passed=False,error=repr(e));print(json.dumps(row),flush=True)
            rows.append(row);save()
            if not row['passed']:break
    finally:device.close()
    raise SystemExit(0 if save() else 1)
