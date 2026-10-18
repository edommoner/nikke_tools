"""Read-only CPU witness for the staged Rapunzel HP divergence."""
import importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('survival_probe',ROOT/'scripts/verify-staged-survival.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
name,b,extra=next(x for x in m.fixtures() if x[0]=='raw-new-라푼젤-no-shot')
rows=[]
def trace(frame,event,arg):
    if frame.f_code.co_name=='_live_sum' and event=='return':
        local=frame.f_locals
        if local.get('stat')=='heal_received_pct' and 15.3<local.get('t',-1)<15.4:
            bm=local['self'];rows.append(dict(query='heal_received',result=arg,who=local.get('name'),active=[dict(caster=a.caster,stat=a.effect.get('stat'),name=a.effect.get('name'),targets=a.target_chars,stack=a.stack) for a in bm._active if a.effect.get('stat')=='heal_received_pct']))
    if frame.f_code.co_name=='handle_heal_hp_pct':
        local=frame.f_locals;t=local.get('t',-1)
        if 15.3<t<15.4 and event in ('line','return'):
            bm=frame.f_back.f_locals.get('self')
            row=dict(event=event,line=frame.f_lineno,values={k:local[k] for k in ('caster','t','val','name','base_hp','max_hp','heal_base','heal','target_names') if k in local})
            if bm and hasattr(bm,'state'):
                row['hp_pct']=dict(bm.state.get('hp_pct',{}))
            rows.append(row)
    return trace
with m.v.context(name,extra):
    old=sys.gettrace()
    try:sys.settrace(trace);m.v.v.a.evaluate(b)
    finally:sys.settrace(old)
(ROOT/'research/detail-staged-survival-heal-cpu-witness.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,ensure_ascii=True))
