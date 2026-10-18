import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('buff_preflight',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
rows=[]
for n,b,e in v.fixtures():
 with v.v.t.raw.injected_effects(e):
  c=v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=v.a.evaluate(b)
 row=dict(name=n,effects=len(c['program']['effects']),boss_rows=c['program']['boss_effect_rows'],cpu_total=cpu['total_damage'],dispels=[r for r in cpu['boss_timeline'] if r['event']=='dispel'])
 rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
(ROOT/'research/detail-boss-buffs-cpu-preflight.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
