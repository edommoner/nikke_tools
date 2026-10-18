"""Run independent CPU battle fixtures before GPU differential tests."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('cpu_boss_clock',ROOT/'scripts/verify-boss-clock-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
rows=[]
for name,body,extra in v.fixtures():
    with v.t.raw.injected_effects(extra):r=v.a.evaluate(body)
    rows.append(dict(name=name,total=r['total_damage'],events=len(r['boss_timeline']),timeline=r['boss_timeline']))
(ROOT/'research/detail-boss-clock-cpu-preflight.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{k:r[k] for k in ('name','total','events')} for r in rows]))
