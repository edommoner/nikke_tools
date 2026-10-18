"""Measure actual CPU lifecycle histories for the intended long-run fixtures."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('boss_history',ROOT/'scripts/verify-boss-clock-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from detail_boss import validate_patterns
rows=[]
for name,body,extra in v.fixtures(long=True):
    en={**body['enemy'],'optimal_range_weapons':body['enemy'].get('optimal_range_weapons',[])}
    boss=v.BossScript(validate_patterns(en['patterns']),en,lambda caster,code:False)
    boss.begin_frame(0,en);at=0
    while at<=180:boss.begin_frame(at,en);at+=1/60
    boss.finish(180)
    rows.append(dict(name=name,log_entries=len(boss.log),maximum_node_ends=max(map(len,boss._ends.values()))))
(ROOT/'research/detail-boss-clock-history-preflight.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows))
