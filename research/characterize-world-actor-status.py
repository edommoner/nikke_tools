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

def main():
 results=[];original_activate=BuffManager._activate;original_finish=BossScript.finish
 for case in fixtures():
  captured={}
  def activated(manager,*args,**kwargs):captured['manager']=manager;return original_activate(manager,*args,**kwargs)
  def finished(boss,*args,**kwargs):
   manager=captured['manager'];carriers=[]
   for ab in manager._active:
    key=getattr(ab,'enemy_recipient_key',None)
    carriers.append(dict(name=ab.effect.get('name',''),stat=ab.effect.get('stat'),caster=ab.caster,targets=list(ab.target_chars or []),recipient_keys=[] if key is None else [dict(label=b.label,kind=int(b.actor.kind),identity=b.actor.identity,generation=b.actor.generation) for b in key.bindings],stack=ab.stack,activated=ab.activated_at,end=ab.expires_at))
   captured['carriers']=carriers;captured['used']=[dict(target=k[0],name=k[1],used=v) for k,v in manager._immune_used.items()];return original_finish(boss,*args,**kwargs)
  with patch.object(BuffManager,'_activate',activated),patch.object(BossScript,'finish',finished):native=observe(case)
  carriers=captured['carriers'];marks=[x for x in carriers if x['name']=='mark'];seed=[x for x in carriers if x['name']=='seed'];counts={}
  for c in carriers:counts[c['name']]=counts.get(c['name'],0)+1
  results.append(dict(name=case['name'],carrier_count_by_name=counts,mark_count=len(marks),mark_stack_distribution={str(n):sum(c['stack']==n for c in marks) for n in sorted({c['stack'] for c in marks})},charge_used=captured['used'],shared_seed=seed,damage=native['damage']))
 by={r['name']:r for r in results}
 assert by['128-global-immunity']['mark_count']==0
 assert by['65-current-generation-immune-recipients']['mark_count']==63
 assert by['128-named-immunity-mark']['mark_count']==0 and by['128-named-immunity-other']['mark_count']==128
 assert not by['irremovable-bypasses-count-immunity']['charge_used'] and by['irremovable-bypasses-count-immunity']['mark_count']==128
 for n in (1,65,128):
  shared=by['one-shared-initialized-carrier-'+str(n)]['shared_seed'];assert len(shared)==1 and shared[0]['stack']==3 and len(shared[0]['targets'])==n and len(shared[0]['recipient_keys'])==n
 assert by['count-name-pool-max-across-two-owners']['charge_used']==[dict(x) for x in by['128-count-immunity-2']['charge_used']]
 for cap,used,stack in [(0,0,4),(.5,1,3),(1,1,3),(1.5,2,2),(2,2,2)]:
  row=by['128-count-immunity-'+str(cap)];assert row['mark_stack_distribution']=={str(stack):128} and len(row['charge_used'])==(128 if used else 0) and all(x['used']==used for x in row['charge_used'])
 assert len(by['distinct-count-names-have-independent-pools']['charge_used'])==256 and by['distinct-count-names-have-independent-pools']['mark_stack_distribution']=={'1':128}
 assert by['charge-refresh-rearms-one-pool-per-target']['mark_count']==0 and len(by['charge-refresh-rearms-one-pool-per-target']['charge_used'])==128
 report=dict(passed=True,scope='Actual full CPU simulate with128 typed recipients',cases=results,gpu_executions=0,cpu_runtime_state_used_as_gpu_input=False,shared_initialization_requires_multi_recipient_canonical_resident=True,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-actor-status-native-contract.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Native typed128 status contracts',len(results),'shared1/65/128 recipient resident confirmed;GPU calls0')
if __name__=='__main__':main()
