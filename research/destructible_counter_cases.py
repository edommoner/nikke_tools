"""Authored resolved landings and real counter completion children."""
import copy
from target_counter_cases import marker
from destructible_world_cases import binding,tick,hit,select

def fixtures():
 rows=[]
 def add(name,kind=2,capacity=1000,threshold=2,ops=None,owner=None,**policy):
  m=marker(threshold=threshold,actor=dict(kind={2:'projectile',3:'hp_shield',4:'hit_shield'}[kind],identity=10,generation=1),**policy)
  m['trigger']['timing']=['battle_start']
  child=dict(name='reward',source='스킬2',type='buff',stat='atk_pct',fixed_value=11,target='self',duration=10,max_stack=10,trigger=dict(timing=['event:target_counter_complete:marker'],condition=[]))
  c=dict(name='destructible-counter/'+name,nodes=[dict(id='a',until=dict(targets_cleared=True))],bindings=[binding(kind=kind,capacity=capacity,**({'owner':owner} if owner else {}))],ops=ops or [tick(0),hit(.1,kind=kind,amount=1),hit(.2,kind=kind,amount=1)],effects=[m,child]);rows.append(c);return c
 add('threshold-projectile-live')
 add('break-projectile-death',capacity=10,threshold=99,ops=[hit(amount=100),select(.1)],owner=[5,77,3])
 add('break-hp-shield',kind=3,capacity=10,threshold=99,ops=[hit(kind=3,amount=100),select(.1)])
 add('fractional-hit-shield',kind=4,capacity=2,threshold=99,ops=[hit(kind=4,credit=.5),hit(.1,kind=4,credit=.5),hit(.2,kind=4,amount=0,credit=1),select(.3)])
 add('blocked-hit-credit',kind=4,capacity=2,threshold=1,outcomes=['blocked'],ops=[hit(kind=4,amount=0,outcome=1),select(.1)])
 add('miss-no-credit',ops=[hit(amount=0,credit=0,outcome=0),select(.1)])
 add('broken-stale-reentry',capacity=10,threshold=99,ops=[hit(amount=100),hit(amount=100),select(.1)])
 add('death-without-reward',capacity=10,threshold=99,on_death=False,ops=[hit(amount=100),select(.1)])
 c=add('threshold-refresh-before-dead-retirement',capacity=10,threshold=1,ops=[hit(amount=100),select(.1)])
 c['effects'][0]['trigger']['timing'].append('event:target_counter_complete:marker');c['effects'][0]['max_trigger']=2
 c=add('live-refresh-survives-parent',threshold=1)
 c['effects'][0]['trigger']['timing'].append('event:target_counter_complete:marker');c['effects'][0]['max_trigger']=2
 c=add('owner-policy-and-descriptive-target-owner',attackers='owner',owner=[5,77,3],ops=[hit(amount=1),hit(.1,amount=1),hit(.2,amount=1)])
 c['who']=[2,0,0]
 c=add('old-generation-does-not-credit',ops=[tick(0),tick(.2),hit(.2,generation=1,amount=1),[4,0,0,0,0,.2,0,0,0],hit(.3,generation=2,amount=1)])
 c['nodes']=[dict(id='a',after=['start','a'],repeat=2,until=dict(time=.2))]
 second=copy.deepcopy(c['effects'][0]);second.update(name='next');second['target_counter']['actor']['generation']=2;second['trigger']['timing']=['on_attack'];second['target_counter']['threshold']=1
 c['effects']=[c['effects'][0],second,c['effects'][1]];c['effects'][-1]['trigger']['timing'].append('event:target_counter_complete:next')
 c=add('siblings-latched-before-refresh-and-break',capacity=10,threshold=1,ops=[hit(amount=100),select(.1)])
 first=copy.deepcopy(c['effects'][0]);first['name']='first'
 second=copy.deepcopy(c['effects'][0]);second['name']='second';second['trigger']['timing'].append('event:target_counter_complete:first');second['max_trigger']=2
 reward=c['effects'][1];reward['trigger']['timing']=['event:target_counter_complete:first','event:target_counter_complete:second']
 c['effects']=[first,second,reward]
 return rows
