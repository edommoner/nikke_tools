"""Authored128-target immunity/cleanse cases shared by both GPU backends."""
import copy,importlib.util
from pathlib import Path

def fixtures(recipient):
 root=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('status_contracts',root/'characterize-world-actor-status.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows=copy.deepcopy(m.fixtures())
 for c in rows:c.update(observe_enemy_fields=True,observe_named_state=True,allow_shared_enemy_fields=True,observe_actor_status=True,state_queries=[(0,0,0,1,'mark'),(0,5,0,1,'mark'),(0,5,64,1,'mark'),(0,5,126,1,'mark')])
 base=copy.deepcopy(rows[0]);e=recipient.state.fields.pool.body.f.effect
 def add(name,effects,owners=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners or [0]*len(effects));rows.append(c);return c
 def harmful(name='mark',duration=-1):return e('received_dmg_pct',5,name=name,target='all_enemies',polarity='harmful',max_stack=3,duration=duration)
 def cleanse(limit,target='all_enemies',**kw):return dict(name='cleanse',source='스킬1',type='instant',stat='debuff_cleanse',fixed_value=limit,target=target,trigger=dict(timing=['on_attack'],condition=[]),**kw)
 for limit in (0.,-.5,.5,1.,1.5,2.,1e308,-1e308):add('typed-cleanse-limit-'+repr(limit),[harmful(),harmful('second'),cleanse(limit)])
 for target in ('boss','target','enemies_top_atk:65','enemies_top_hp:2','enemies_lowest_hp:1','enemies_nearest:2','enemies_top_def:2'):
  add('typed-cleanse-scope-'+target,[harmful(),cleanse(1,target)])
 add('irremovable-not-cleaned',[e('received_dmg_pct',5,name='mark',target='all_enemies',polarity='harmful_irremovable'),harmful('ordinary'),cleanse(0)])
 add('beneficial-fields-not-cleaned',[e('received_dmg_pct',5,name='beneficial',target='all_enemies',polarity='beneficial'),harmful(),cleanse(0)])
 c=add('empty-shared-harmful-keeps-cleanse-silent',[dict(harmful(),trigger=dict(timing=['event:full_reload'],condition=[])),dict(name='init',source='스킬1',type='instant',stat='buff_stack_init',target_effect='mark',target='all_enemies',fixed_value=2,max_trigger=1,trigger=dict(timing=['battle_start'],condition=[])),cleanse(1),e('atk_pct',5,name='should-not-trigger',target='self',trigger=dict(timing=['event:state_end:mark'],condition=[]))])
 for stat in ('debuff_immune','debuff_immune_count'):
  c=add('reopened-callback-immunity-'+stat,[e(stat,100,name='charges',target='all_enemies'),dict(harmful(),trigger=dict(timing=['event:target_spawn'],condition=[]))]);c['patterns'][0]['spec']['count']=3;c['patterns'][0].update(after=['start','wave'],until=dict(time=.1),repeat=0,emit=['event:target_spawn']);c['duration']=.25;c['state_queries']=[(0,0,0,1,'mark'),(0,5,0,3,'mark')]
 return rows
