"""Observe the ordinary fixture without any stress-only skill injection."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('scaling_ui_cpu',ROOT/'scripts/verify-staged-survival-scaling.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
b=json.loads((ROOT/'research/detail-survival-scaling-api-fixture.json').read_text(encoding='utf-8'));b.update(compute_backend='cpu',verify_detail=False)
original=v.s.timeline.simulate;seen={'minimum_HP':100}
def trace(frame,event,arg):
    if frame.f_code is original.__code__ and event=='line' and 'state' in frame.f_locals:
        pct=frame.f_locals['state'].get('hp_pct',{}).get('목단')
        if pct is not None:seen['minimum_HP']=min(seen['minimum_HP'],pct)
    if frame.f_code is original.__code__ and event=='return':
        state=frame.f_locals['state'];seen.update(hp_pct=dict(state['hp_pct']),down=sorted(state.get('down',set())))
    return trace
old=sys.gettrace();sys.settrace(trace)
try:result=v.s.v.v.a.evaluate(b)
finally:sys.settrace(old)
assert 0<seen['minimum_HP']<100 and not seen['down'],seen
print(json.dumps(dict(total=result['total_damage'],final=seen,no_injected_support=True),ensure_ascii=True))
