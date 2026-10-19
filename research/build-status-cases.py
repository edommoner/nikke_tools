"""Authored immunity/cleanse stimuli, shared unchanged by both GPU backends."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def buff(name='harm',**kw):
 e=dict(name=name,source='스킬1',type='buff',stat='atk_pct',fixed_value=-10,target='all_allies',duration=2,max_stack=5,polarity='harmful',trigger=dict(timing=['on_attack'],condition=[]));e.update(kw);return e
def immune(stat='debuff_immune_count',**kw):
 e=buff('immune',stat=stat,fixed_value=1,target='all_allies',polarity='beneficial',trigger=dict(timing=['event:full_reload'],condition=[]));e.update(kw);return e
def cleanse(**kw):
 e=dict(name='cleanse',source='스킬2',type='instant',stat='debuff_cleanse',target='all_allies',trigger=dict(timing=['hit_count'],condition=[]));e.update(kw);return e
def notify(t,event=19,who=0):return [t,0,event,who,0,-1,0,0]
def query(t,i=0,target=0):return [t,2,0,0,target,i,0,0]
def case(name,effects,script,**kw):
 c=dict(name='status-'+name,effects=effects,script=script,expected_queries=[dict(time=r[0]) for r in script if r[1]==2],combat=dict(weapons=[dict(enabled=False) for _ in range(5)],targets=[dict(hp=100000)]),stack_reference=True,status_reference=True);c.update(kw);return c
def fixtures():
 rows=[]
 def add(name,effects,script,**kw):rows.append(case(name,effects,script,**kw));return rows[-1]
 for limit in (None,0.,-0.,-.5,.5,1.,1.9,2.,-1.,1e308,-1e308):
  op=cleanse();
  if limit is not None:op['fixed_value']=limit
  for target in ('self','all_allies'):
   op=dict(op,target=target)
   effects=[buff('first'),buff('second'),buff('third'),buff('benefit',polarity='beneficial',fixed_value=10),buff('irremovable',polarity='harmful_irremovable')]
   observer=buff('end observer',polarity='beneficial',fixed_value=100,trigger=dict(timing=['event:state_end:first'],condition=[]))
   add('cleanse-limit-'+str(limit)+'-'+target,[*effects,op,observer],[notify(0,7),notify(.1,8),query(.1)])
 for stat in ('debuff_immune','debuff_immune:harm','debuff_immune:other','debuff_immune_count'):
  add('application-'+stat,[immune(stat),buff()],[notify(0),notify(.1,7),query(.1),notify(.2,7),query(.2,1)])
 for value in (0.,-.5,.5,1.,1.5,2.,1e308):
  e=immune();e['fixed_value']=value
  add('charge-cap-'+str(value),[e,buff()],[notify(0)]+sum(([notify(i/10,7),query(i/10,i-1)] for i in range(1,5)),[]))
 for mode in ('refresh','remove-reapply','remove-init','expiry-reapply','expiry-init'):
  e=immune(target='self',duration=.2)
  harm=buff(target='self');remove=dict(cleanse(name='remove immunity',target_effect='immune'),stat='remove_named_buff',trigger=dict(timing=['hit_count'],condition=[]))
  init=dict(cleanse(name='init immunity',target_effect='immune'),stat='buff_stack_init',fixed_value=1,trigger=dict(timing=['full_charge_fire'],condition=[]))
  script=[notify(0),notify(.05,7)]
  if mode.startswith('remove'):script.append(notify(.1,8))
  if mode.startswith('expiry'):script.insert(0,[0,4,0,0,0,-1,0,0]);script.extend([[.1,4,0,0,0,-1,0,0],[.2,4,0,0,0,-1,0,0]])
  script.extend([notify(.3,11 if mode.endswith('init') else 19),notify(.4,7),query(.4)])
  add('charge-'+mode,[e,harm,remove,init],script)
 for duplicate in (False,True):
  a=immune();b=immune();b['fixed_value']=2;b['source']='스킬2';b['name']='immune' if duplicate else 'other immunity'
  add('pools-max-not-sum-'+str(duplicate),[a,b,buff()],[notify(0)]+[notify(i/10,7) for i in range(1,5)]+[query(.4)])
 for lazy in (False,True):
  e=immune();e['target']='allies_top_atk:1' if lazy else 'self'
  add('immune-lazy-presence-'+str(lazy),[e,buff(target='self')],[notify(0),notify(.1,7),query(.1),notify(.2,7),query(.2,1)])
 for expiry in (False,True):
  e=immune('debuff_immune');e['duration']=.1
  add('immune-expired-unretired-'+str(expiry),[e,buff()],[notify(0)]+([[0,4,0,0,0,-1,0,0],[.1,4,0,0,0,-1,0,0]] if expiry else [])+[notify(.2,7),query(.2)])
 gate=buff('gate',polarity='beneficial',fixed_value=1,duration=-1,trigger=dict(timing=['event:full_reload'],condition=[]))
 e=immune('debuff_immune');e['duration']=-1;e['trigger']['condition']=['self_state:gate']
 remove=dict(cleanse(name='remove gate',target_effect='gate'),stat='remove_named_buff',trigger=dict(timing=['hit_count'],condition=[]))
 add('immune-runtime-false-still-presence',[gate,e,remove,buff()],[notify(0),notify(.1,8),notify(.2,7),query(.2)])
 for stat in ('debuff_immune','debuff_immune_count'):
  e=immune(stat);e['target']='all_enemies';h=buff(target='all_enemies',stat='received_dmg_pct');c=add('enemy-generation-'+stat,[e,h],[notify(0),notify(.1,7),query(.1),[.2,22,0,0,1,-1,0,0],[.3,21,0,0,1,-1,100000,0],notify(.4,7),query(.4,1,1),query(.4,2,0)])
  c['combat']['targets']=[dict(hp=100000),dict(hp=100000,kind=5,identity=0)]
 for target in ('self','allies_top_atk:1','all_enemies'):
  e=buff('marker',stat=None,polarity='harmful',target=target)
  add('marker-cleanse-'+target,[e,cleanse(target=target)],[notify(0,7),notify(.1,8),query(.1)])
 from status_case_extensions import cases as extended
 rows+=extended(buff,immune,cleanse,notify,query,case)
 former=json.loads((R/'tests/fixtures/portable-lazy-capacity-rejection.json').read_text());former.update(stack_reference=True,status_reference=True,status_damage_reference=True);rows.append(former)
 return rows
if __name__=='__main__':
 rows=fixtures();(R/'tests/fixtures/portable-status.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n');print('Authored status cases',len(rows))
