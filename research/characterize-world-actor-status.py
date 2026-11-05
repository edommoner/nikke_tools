"""Full native battles:wide immunity pools and shared initialization contracts.
No GPU calls;the resulting runtime state is evidence,never a GPU input.
"""
import copy,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('typed_status_state',ROOT/'research/verify-world-actor-state.py');state=importlib.util.module_from_spec(s);s.loader.exec_module(state)
from calculator.buff_manager import BuffManager
from calculator.boss_pattern import BossScript
from world_frame_native import observe

def fixtures():
 base=copy.deepcopy(state.fields.fixtures()[0]);base.update(observe_enemy_fields=False,observe_named_state=False,duration=.35);base['patterns'][0]['spec'].update(count=127,hp=100000000);rows=[]
 def effect(stat,value,name,target='all_enemies',timing='battle_start',**kw):return state.fields.pool.body.f.effect(stat,value,name=name,target=target,trigger=dict(timing=[timing],condition=[]),**kw)
 def marker(**kw):return effect('received_dmg_pct',0,'mark',timing='on_attack',max_stack=20,polarity='harmful',**kw)
 def add(name,effects,owners=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners or [0]*len(effects));rows.append(c);return c
 add('128-global-immunity',[effect('debuff_immune',0,'immune'),marker()])
 add('65-current-generation-immune-recipients',[effect('debuff_immune',0,'immune',target='enemies_top_atk:65'),marker()])
 for name in ('mark','other'):
  add('128-named-immunity-'+name,[effect('debuff_immune:'+name,0,'immune'),marker()])
 for cap in (0,.5,1,1.5,2):add('128-count-immunity-'+str(cap),[effect('debuff_immune_count',cap,'charges'),marker()])
 add('count-name-pool-max-across-two-owners',[effect('debuff_immune_count',1,'charges'),effect('debuff_immune_count',2,'charges'),marker()],owners=[0,1,0])
 add('distinct-count-names-have-independent-pools',[effect('debuff_immune_count',1,'first'),effect('debuff_immune_count',2,'second'),marker()])
 add('zero-valued-count-carrier-still-has-state',[effect('debuff_immune_count',0,'charges'),marker()])
 add('charge-refresh-rearms-one-pool-per-target',[effect('debuff_immune_count',1,'charges',timing='on_attack'),marker()])
 add('irremovable-bypasses-count-immunity',[effect('debuff_immune_count',20,'charges'),effect('received_dmg_pct',0,'mark',timing='on_attack',max_stack=20,polarity='harmful_irremovable')])
 for target,count in [('boss',1),('all_enemies',128),('enemies_top_atk:65',65)]:
  template=effect('received_dmg_pct',0,'seed',target=target,timing='event:full_reload',max_stack=5,duration=2)
  operation=dict(name='init',source='스킬1',type='instant',stat='buff_stack_init',target_effect='seed',target=target,fixed_value=3.9,max_trigger=1,trigger=dict(timing=['battle_start'],condition=[]))
  add('one-shared-initialized-carrier-'+str(count),[template,operation])
 return rows
