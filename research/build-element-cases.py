"""Authored element-override stimuli and independent integer expectations."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def buff(name,stat='',value=None,**kw):
 e=dict(name=name,type='buff',source='스킬1',stat=stat,target='self',duration=1,trigger=dict(timing=['battle_start'],condition=[]));e.update(kw)
 if value is not None:e['fixed_value']=value
 return e

def build(name,*,world='전격',code='전격',base=False,owner=0,target='self',value=None,duration=1,timing='battle_start',conditions=(),present=False,lose=False,reapply=False,stack=1,aim=False,bonus=0,collision=False):
 marker=buff('override','element_code_override',value,target_code=code,target=target,duration=duration,max_stack=stack,trigger=dict(timing=[timing]+(['on_attack'] if reapply else []),condition=list(conditions)))
 effects=[buff('전격' if collision else 'no critical','crit_rate',-15,target='all_allies',duration=-1),marker];owners=[0,owner]
 if bonus:effects.append(buff('element bonus','element_bonus_pct',bonus,target='all_allies',duration=-1));owners.append(0)
 if present:effects.insert(1,buff('gate',duration=.5 if lose else -1));owners.insert(1,owner)
 times=[0,.25,1.249,1.25] if reapply else [0,.999,1,1.001]
 script=[];expected=[];total=[0]*5
 for q,t in enumerate(times):
  script.append([t,4,0,0,0,-1,0,0])
  if q==0 and aim:script.append([t,20,0,0,1,-1,0,0])
  if reapply and q==1:script.append([t,0,7,owner,0,-1,0,0])
  initial=not conditions or present or timing=='passive' and duration==-1
  active=initial and (duration<0 or timing=='passive' and present or t<(1.25 if reapply else 1))
  for who in range(5):
   members=target=='all_allies' or target=='all_allies_excl_self' and who!=owner or target=='self' and who==owner or isinstance(target,list) and who==owner
   match=base or active and bool(world) and world==code and members
   factor=1.1+bonus/100 if match else 1
   total[who]+=int(1000*factor);script.append([t,18,0,who,0,-1,100,0])
  script.append([t,2,0,0,-1,q,0,0]);expected.append(dict(damage=total.copy()))
 return dict(name='element-'+name,element_override_reference=True,effects=effects,owners=owners,combat=dict(weapons=[dict(enabled=False,element_match=base) for _ in range(5)],targets=[dict(hp=1e9)]+([dict(kind=5,hp=1e9)] if aim else []),trace='full'),environment=dict(enemy_code=world),script=script,expected_queries=expected)

cases=[]
for wi,world in enumerate([None,'','전격','작열','unknown:code']):
 for ci,code in enumerate([None,'','전격','unknown:code',' 전격 ']):
  for base in (False,True):cases.append(build(f'matrix-{wi}-{ci}-{base}',world=world,code=code,base=base))
for owner in range(5):
 for target in ('self','all_allies','all_allies_excl_self'):cases.append(build(f'recipients-{owner}-{target}',owner=owner,target=target))
for vi,value in enumerate((None,0,-10,100)):
 for stack in (1,5):cases.append(build(f'presence-{vi}-{stack}',value=value,stack=stack,reapply=True))
for duration in (-1,1):
 for timing in ('passive','battle_start'):
  for present in (False,True):
   for owner in (0,4):cases.append(build(f'condition-{duration}-{timing}-{present}-{owner}',duration=duration,timing=timing,owner=owner,conditions=['self_state:gate'],present=present))
for timing in ('passive','battle_start'):cases.append(build('state-expired-'+timing,duration=-1,timing=timing,conditions=['self_state:gate'],present=True,lose=True))
for target in ('allies_top_atk:1','allies_lowest_hp:1'):cases.append(build('unresolved-'+target,target=target))
for count in (2,21):cases.append(build('duplicate-'+str(count),target=['self']*count))
for world in ('전격','작열'):
 for base in (False,True):cases.append(build('add-aim-'+world+'-'+str(base),world=world,base=base,aim=True))
for family in ('damage','bonus_damage','burst_damage','split_damage','dot_damage','auto_damage','armor_break_damage','armor_break_burst_damage','sequential_damage','projectile_attachment_damage','projectile_explosion_damage','pierce_damage','core_damage'):
 for world in ('전격','작열'):
  c=build('packet-'+family+'-'+world,world=world);c['effects'].append(dict(name='packet',type='damage',stat=family,source='스킬1',fixed_value=100,target='boss',trigger=dict(timing=['on_attack'],condition=[])));c['owners'].append(0);c['script']=[[0,4,0,0,0,-1,0,0]];c['expected_queries']=[];total=0
  for q,t in enumerate((.1,.2,1)):
   c['script'] += [[t,4,0,0,0,-1,0,0],[t,0,7,0,0,-1,0,0],[t,2,0,0,-1,q,0,0]]
   total+=(2200 if family=='core_damage' else 1100) if world=='전격' and t<1 else (2000 if family=='core_damage' else 1000)
   c['expected_queries'].append(dict(damage=[total,0,0,0,0]))
  if family=='dot_damage':
   c['effects'][1]['duration']=.5;c['effects'][-1].update(duration=1,tick_interval=.25)
   c['script']=[[0,4,0,0,0,-1,0,0],[.1,4,0,0,0,-1,0,0],[.1,0,7,0,0,-1,0,0]];c['expected_queries']=[];total=0
   for q,t in enumerate((.35,.6,.85,1.1)):
    c['script'] += [[t,4,0,0,0,-1,0,0],[t,2,0,0,-1,q,0,0]]
    total+=1100 if world=='전격' and q<2 else 1000
    c['expected_queries'].append(dict(damage=[total,0,0,0,0]))
  cases.append(c)
for base in (False,True):cases.append(build('bonus-'+str(base),base=base,bonus=20))
cases.append(build('name-id-zero',collision=True))
for same_name in (False,True):
 for same_source in (False,True):
  for world in ('전격','작열'):
   c=build(f'alias-{same_name}-{same_source}-{world}',world=world,reapply=True)
   first=c['effects'][1];first['trigger']['timing']=['battle_start']
   other=copy.deepcopy(first);other.update(name=first['name'] if same_name else 'second-override',source=first['source'] if same_source else '스킬2',target_code='작열',trigger=dict(timing=['on_attack'],condition=[]))
   c['effects'].append(other);c['owners'].append(0);total=[0]*5;c['expected_queries']=[]
   for q in range(4):
    match=(world=='전격' and (q<3 if same_name else q<2)) or world=='작열' and not same_name and 1<=q<3
    total=[v+(1100 if i==0 and match else 1000) for i,v in enumerate(total)]
    c['expected_queries'].append(dict(damage=total.copy()))
   cases.append(c)
authored=json.loads((R/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())
for character,es in authored.items():
 for e in es:
  if e.get('stat')!='element_code_override':continue
  for world in (e['target_code'],'unmatched',None):
   c=build('authored-'+character+'-'+str(world),world=world,code=e['target_code'],duration=e['duration'])
   c['effects'][1]=copy.deepcopy(e);c['authored_effect_character']=character
   cases.append(c)
for missing in (False,True):
 c=build('capacity-256-'+str(missing),world='code:edge',code=None if missing else 'code:edge')
 for i in range(253):c['effects'].append(buff('padding-'+str(i),duration=-1));c['owners'].append(0)
 cases.append(c)
for world in ('전격','작열'):
 for owner in (0,4):
  for target in ('self','all_allies','allies_top_atk:1'):
   c=build(f'physical-bullets-{world}-{owner}-{target}',world=world,owner=owner,target=target,duration=-1)
   c['element_physical_reference']=True;c['effects'][1]['duration_bullets']=2
   c['combat']['weapons'][0].update(enabled=True,capacity=10,interval=.25,reload=1,coefficient=100,gauge=0)
   c['script']=[];c['expected_queries']=[];total=0
   for q,t in enumerate((0,.25,.5,.75)):
    matches=world=='전격' and (target=='all_allies' or target=='self' and owner==0 or target=='allies_top_atk:1')
    advantage=matches and (q==2 if target=='allies_top_atk:1' else q<3)
    total+=1100 if advantage else 1000
    c['script'] += [[t,4,0,0,0,-1,0,0],[t,2,0,0,-1,q,0,0]]
    c['expected_queries'].append(dict(damage=[total,0,0,0,0]))
   cases.append(c)
assert len({c['name'] for c in cases})==len(cases)
(R/'tests/fixtures/portable-element-overrides.json').write_text(json.dumps(dict(cases=cases),ensure_ascii=False,indent=2)+'\n');print(len(cases),'authored element cases')
