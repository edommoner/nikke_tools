"""Observe the negative revive control before changing its inaccurate test name."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('Rei_dead_first_probe',ROOT/'scripts/verify-staged-decoy-healing.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
name,b,extra=next(x for x in v.real_fixtures() if x[0].endswith('dead-first-B1'));b['compute_backend']='cpu';seen={};code=v.v.s.timeline.simulate.__code__
def trace(frame,event,arg):
    if frame.f_code is not code:return None
    if event=='return':
        state=frame.f_locals['state'];seen.update(down=sorted(state.get('down',set())),HP=dict(state['hp']),HP_pct=dict(state['hp_pct']))
    return trace
old=sys.gettrace();sys.settrace(trace)
try:
    with v.v.s.v.context(name,extra):r=v.v.s.v.v.a.evaluate(b)
finally:sys.settrace(old)
assert '라이' in seen['down'],seen
p=dict(cpu_observed=True,gpu_verified=False,objective_complete=False,case=name,total=r['total_damage'],final=seen,bursts=r['burst_timeline'],source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['research/probe-rei-dead-first-CPU.py','scripts/verify-staged-decoy-healing.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']})
(ROOT/'research/detail-Rei-dead-first-cpu-probe.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(total=p['total'],final=p['final'],bursts=p['bursts']),ensure_ascii=True))
