"""Positive CPU control: the weapon-list fixture actually enters a weapon mode."""
import importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('mode_witness',ROOT/'scripts/verify-boss-clock-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from calculator.timeline import CharState
counts={};original=CharState._tick_weapon_change
def observed(self,*args,**kwargs):
 counts[self.name]=counts.get(self.name,0)+1
 return original(self,*args,**kwargs)
n,b,e=list(v.fixtures())[13]
with v.t.raw.injected_effects(e),patch.object(CharState,'_tick_weapon_change',observed):cpu=v.a.evaluate(b)
report={'passed':bool(counts),'fixture':n,'duration':b['duration'],'mode_ticks':counts,'cpu_total':cpu['total_damage']}
(ROOT/'research/detail-boss-clock-mode-witness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=True));assert report['passed']
