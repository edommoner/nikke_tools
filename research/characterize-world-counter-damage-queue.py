"""Native creation/landing timing and damage basis for completion damage children."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from effect_runtime import state
from world_frame_native import observe
s=importlib.util.spec_from_file_location('damage_queue_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
def fixtures():
 sources={c['name']:c for c in physical.fixtures()};rows=[]
 for source in ('body-completion-versus-lifesteal-order','add-completion-versus-lifesteal-order','add-survives-completion-versus-lifesteal-order'):
  for duration in (.01,.15):
   c=copy.deepcopy(sources[source]);c.update(name=source+'-damage-child-duration-'+str(duration),duration=duration)
   c['effects'][-1]=dict(name='queued-child',source='스킬1',type='damage',stat='bonus_damage',fixed_value=25,target='target',trigger=dict(timing=['event:target_counter_complete:marker'],condition=[]));rows.append(c)
 base=copy.deepcopy(rows[-1])
 for target in ('boss','target'):
  c=copy.deepcopy(base);c['name']='completion-damage-body-basis-field-'+target
  c['effects'].insert(-1,dict(name='basis-field',source='스킬1',type='buff',stat='received_dmg_pct',fixed_value=25,target=target,duration=.3,trigger=dict(timing=['event:target_counter_complete:marker'],condition=[])));c['owners'].insert(-1,0);rows.append(c)
 c=copy.deepcopy(rows[2]);c['name']='named-skill-hit-child-inherits-lethal-add-completion-target'
 c['effects'].append(dict(name='queued-context-probe',source='스킬1',type='buff',stat='lifesteal_pct',fixed_value=40,target='self',duration=.3,trigger=dict(timing=['hit_count:queued-child:1'],condition=['target_is_add'])));c['owners'].append(0);rows.append(c)
 c=copy.deepcopy(rows[2]);c['name']='queued-skill-allied-runtime-condition-queries-body'
 c['effects'].insert(-1,dict(name='body-query-attack',source='스킬1',type='buff',stat='atk_pct',fixed_value=100,target='self',duration=-1,trigger=dict(timing=['passive'],condition=['target_state:marker'])));c['owners'].insert(-1,0);rows.append(c)
 c=copy.deepcopy(c);c['name']='queued-skill-body-query-with-neutral-enemy-field'
 c['effects'].insert(0,dict(name='query-scope-witness',source='스킬1',type='buff',stat='received_dmg_pct',fixed_value=0,target='boss',duration=.3,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].insert(0,0);rows.append(c)
 return rows
