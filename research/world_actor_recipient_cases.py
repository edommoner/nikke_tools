"""Shared initialized carrier lifetime and canonical receiver membership."""
import copy,importlib.util
from pathlib import Path

def fixtures(state):
 r=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('recipient_native_contract',r/'characterize-world-actor-status.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 rows=[copy.deepcopy(c) for c in m.fixtures() if c['name'].startswith('one-shared-initialized-carrier-')]
 for c in rows:c['effects'][0]['values']={'10':10};c.update(observe_enemy_fields=True,observe_named_state=True,allow_shared_enemy_fields=True,state_queries=[(0,0,0,1,'seed'),(0,5,0,1,'seed'),(0,5,64,1,'seed'),(0,5,126,1,'seed')])
 base=copy.deepcopy(rows[1])
 def add(name,operation=None):
  c=copy.deepcopy(base);c['name']=name
  if operation:c['effects'].append(operation);c['owners'].append(0)
  rows.append(c);return c
 def remove(target='all_enemies',scope='target',timing='on_attack'):
  return dict(name='remove',source='스킬1',type='instant',stat='remove_named_buff',target_effect='seed',target=target,remove_scope=scope,trigger=dict(timing=[timing],condition=[]))
 for target in ('boss','target','enemies_top_atk:65','all_enemies'):
  add('shared-partial-removal-'+target,remove(target))
 add('shared-global-removal',remove(scope='global'))
 c=add('shared-death-prunes-only-membership');c['patterns'][0]['spec']['hp']=1300
 c=add('shared-stale-capture-does-not-bind-new-generation',remove(timing='enemy_death'));c['patterns'][0]['spec']['hp']=1300;c['patterns'][0].update(after=['start','wave'],repeat=0,until=dict(targets_cleared=True))
 for value in (0.,-0.,.5,-.5,-1.,9.,2147483647.):
  c=add('shared-init-value-'+repr(value));c['effects'][1]['fixed_value']=value
 c=add('shared-finite-expiry-one-state-end');c['effects'][0]['duration']=.15
 c['effects'].append(state.fields.pool.body.f.effect('atk_pct',1,name='expiry',target='self',max_stack=128,trigger=dict(timing=['event:state_end:seed'],condition=[])));c['owners'].append(0)
 # Normal per-receiver fields and shared initialized seed share the query API.
 c=add('single-and-shared-canonical-membership');c['effects'].append(state.fields.pool.body.f.effect('received_dmg_pct',5,name='ordinary',target='all_enemies'));c['owners'].append(1)
 return rows
