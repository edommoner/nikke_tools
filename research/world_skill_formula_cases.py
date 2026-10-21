"""Native numeric witnesses for world auto versus explicit normal skill formulas."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('skill_formula_source',ROOT/'research/verify-world-skills.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
def fixtures():
 base=next(c for c in suite.fixtures() if c['name']=='direct-family-auto_damage');rows=[copy.deepcopy(base)]
 for name,stat,value,normal,hits in [('auto-normal-only-damage','normal_atk_dmg_pct',50,False,1),('auto-explicit-normal-damage','normal_atk_dmg_pct',50,True,1),('auto-normal-only-critical','normal_atk_crit_rate',50,False,1),('auto-skill-critical','crit_rate',50,False,1),('auto-three-normal-only','normal_atk_dmg_pct',50,False,3),('auto-three-explicit-normal','normal_atk_dmg_pct',50,True,3),('auto-explicit-normal-critical','normal_atk_crit_rate',50,True,1)]:
  c=copy.deepcopy(base);c['name']=name;damage=next(e for e in c['effects'] if e.get('type')=='damage');damage['stat']='auto_damage'+(':3' if hits==3 else '')
  if normal:damage['damage_formula']='normal_attack'
  c['effects'].append(dict(name='formula-witness',source='스킬1',type='buff',stat=stat,fixed_value=value,target='self',duration=-1,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].append(0);rows.append(c)
 return rows
