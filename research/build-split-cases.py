"""Authored split stimuli; native results are observed after GPU readback only."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def buff(name,stat,value=None,target='all_allies',timing='on_attack',condition=(),**kw):
 e=dict(name=name,source='스킬1',type='buff',stat=stat,target=target,duration=-1,max_stack=1,trigger=dict(timing=[timing],condition=list(condition)))
 e.update(kw)
 if value is not None:e['fixed_value']=value
 return e
def notify(t=0,event=7,owner=0):return [t,0,event,owner,0,-1,0,0]
def hit(t=.1,amount=150,mask=1,pierce=False,covered=0):return [t,31,int(pierce),covered,mask,-1,amount,100]
def query(t=.2,index=0):return [t,2,0,0,0,index,0,0]
rows=[]
def add(name,effects,script,owners=None,allies=None):
 rows.append(dict(split_reference=True,name='split-'+name,effects=effects,script=script,expected_queries=[dict(time=c[0]) for c in script if c[1]==2],environment=dict(allies=allies or [dict(base_hp=1000,base_cover_hp=200,cover_hp=200) for _ in range(5)]),**(dict(owners=owners) if owners else {})))
group=lambda **kw:buff('group','received_dmg_split_even',**kw)
for mask in (1,2,4,31):
 for amount in (1,150,999.999999):add('all-'+str(mask)+'-'+str(amount),[group()],[notify(),hit(mask=mask,amount=amount),query()])
for target in ('self','all_allies_excl_self',['self','allies_lowest_hp_excl:2'],['allies_lowest_hp_excl:2','self']):
 add('target-'+str(target),[group(target=target)],[notify(),hit(mask=31),query()])
add('original-defense-only',[group()],[notify(),hit(amount=300,mask=2),query()],allies=[dict(base_hp=1000,base_defense=i*50) for i in range(5)])
add('original-incoming-modifier-only',[group(),buff('resist','received_dmg_pct',-50,target='self')],[notify(),hit(amount=500),query()])
for stat in ('shield_from_max_hp_pct','shared_shield_from_max_hp_pct','decoy','invincible','undying'):
 for pierce in (False,True):
  add('layer-'+stat+'-'+str(pierce),[group(),buff('guard',stat,10 if stat not in ('invincible','undying') else None,target='all_allies_excl_self')],[notify(),hit(amount=1000,pierce=pierce,covered=4),query()])
add('direct-only-hit-notify',[group(),buff('observed','atk_pct',10,target='self',timing='received_hit')],[notify()]+[hit(mask=1<<i) for i in range(5)]+[query()])
add('follower-cover-notify',[group(),buff('observed','atk_pct',10,target='self',timing='event:cover_hit')],[notify(),hit(covered=2),query()],owners=[0,1])
add('overlap-union-not-transitive',[group(target=['self','allies_lowest_hp_excl:2']),buff('other','received_dmg_split_even',target='all_allies_excl_self',timing='event:full_reload')],[notify(),notify(.01,19),hit(),query()])
add('expiry-boundary',[group(duration=.1)],[notify(),hit(),query()])
add('runtime-condition',[group(condition=['during_shield']),buff('guard','shield_from_max_hp_pct',10,target='self')],[notify(),hit(pierce=True),query()])
add('member-downed-before-capture',[group()],[notify(),hit(amount=10000),query(.1,0),hit(.2),query(.2,1)])
add('group-frozen-after-removal',[group(),dict(buff('remove','remove_named_buff',target='all_allies',timing='received_hit'),type='instant',target_effect='group')],[notify(),hit(),query()])
add('member-lethal-callback',[group(),buff('save','undying',target='self',timing='event:lethal_hit')],[notify(),hit(amount=10000),query()],owners=[0,1])
add('one-member-already-down',[group()],[hit(.01,2000,mask=16),notify(.02),hit(.1),query()])
add('groups-recomputed-for-next-primary',[group(),dict(buff('remove','remove_named_buff',target='all_allies',timing='received_hit'),type='instant',target_effect='group')],[notify(),hit(mask=31),query()])
add('duplicate-overlapping-lists',[group(target=['all_allies',['self','all_allies']])],[notify(),hit(mask=31),query()])
add('nested-target-order',[group(target=[['allies_lowest_hp_excl:2'],['self','allies_lowest_hp_excl:2']])],[notify(),hit(mask=31),query()])
add('runtime-member-filter',[group(condition=['during_shield']),buff('guard','shield_from_max_hp_pct',10,target='allies_right:1')],[notify(),hit(pierce=True),query()])
for copies in (10,11,21):
 add('duplicate-audience-'+str(copies),[group(target=['self']*copies,event_scope='recipients'),buff('observed','atk_pct',10,target='self',timing='event:group',max_stack=100)],[notify(),hit(),query()])
add('alias-different-order-stays-separate',[group(target=['self','allies_right:1']),group(target=['allies_right:1','self'],timing='event:full_reload')],[notify(),notify(.01,19),hit(),query()])
add('alias-identical-order-refreshes',[group(target=['self','allies_right:1']),group(target=[['self'],'allies_right:1'],timing='event:full_reload')],[notify(),notify(.01,19),hit(),query()])
(R/'tests/fixtures/portable-split.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n');print(len(rows))
