"""CPU-only whole-squad witnesses for the next lost-HP scaling port (Moran)."""
import ast,hashlib,importlib.util,inspect,json,math,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('lost_hp_cpu_oracle',ROOT/'scripts/verify-survival-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
N=v.N;B=v.B;E=v.E;code=v.timeline.simulate.__code__
lines,first=inspect.getsourcelines(v.timeline.simulate);tree=ast.parse(textwrap.dedent(''.join(lines)))
advance=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT'];assert len(advance)==1
end_line=first+advance[0].lineno-1;rows=[]
for name in ('full-health','half-health','heal-rearms-value','stacks-do-not-multiply','receiver-health-does-not-scale','max-HP-denominator','source-down-buff-remains','source-revives'):
    b=v.v.body(1);b['enemy']['patterns']=[v.lethal(at=.2)] if name.startswith('source-') else []
    extra={n:[] for n in N};extra[N[0]].append(B('lost HP power','atk_pct',1.5,N[1],scaling='lost_hp_pct',**(dict(event='every:0.05s',max_stack=3) if name=='stacks-do-not-multiply' else {})))
    if name in ('half-health','heal-rearms-value','stacks-do-not-multiply','receiver-health-does-not-scale'):
        owner=N[1] if name=='receiver-health-does-not-scale' else N[0]
        extra[owner].append(E('reduce health','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1))
    if name=='heal-rearms-value':extra[N[0]].append(E('restore health','instant','heal_hp_pct',100,event='every:0.4s',max_trigger=1))
    if name=='max-HP-denominator':extra[N[0]].append(B('increase capacity only','max_hp_only_pct',100,event='every:0.2s',max_trigger=1))
    if name=='source-revives':extra[N[2]].append(E('revive source','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
    frames=[]
    def trace(frame,event,arg):
        if frame.f_code is not code:return None
        if event=='line' and frame.f_lineno==end_line:
            local=frame.f_locals;state=local['state'];bm=local['bm'];t=local['t']
            # The authored carrier has a fixed recipient and no random/lazy
            # target; observing its dictionary cannot select battle targets.
            buffs=bm.get_buffs(N[1],'reference-enemy',t)
            frames.append(dict(time=t,caster_hp_pct=state['hp_pct'][N[0]],receiver_hp_pct=state['hp_pct'][N[1]],atk_pct=buffs.get('atk_pct',0),stacks=[a.stack for a in bm._active if a.effect.get('name')=='lost HP power'],source_down=N[0] in state.get('down',set())))
        return trace
    with v.v.context(name,extra):
        old=sys.gettrace()
        try:sys.settrace(trace);cpu=v.v.v.a.evaluate(b)
        finally:sys.settrace(old)
    assert frames
    assert all(math.isclose(f['atk_pct'],1.5*max(0,100-f['caster_hp_pct']),rel_tol=1e-12,abs_tol=1e-9) for f in frames),(name,frames)
    if name not in ('full-health','receiver-health-does-not-scale'):assert any(f['atk_pct']>0 for f in frames),name
    if name=='stacks-do-not-multiply':assert any(f['stacks']==[3] and f['atk_pct']==75 for f in frames)
    if name=='source-down-buff-remains':assert any(f['source_down'] and f['atk_pct']==150 for f in frames)
    if name=='source-revives':assert frames[-1]['atk_pct']==75 and not frames[-1]['source_down']
    rows.append(dict(name=name,cpu_reference_verified=True,gpu_implemented=False,total=cpu['total_damage'],frames=frames));print(json.dumps(dict(name=name,passed=True,gpu_implemented=False)),flush=True)
files=['research/audit-lost-hp-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-lost-hp-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
