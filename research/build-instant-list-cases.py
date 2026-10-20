"""Literal ordered instantaneous-delivery inputs; no CPU quantities are serialized."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def effect(name,stat,value=1,target=None,kind='instant',timing='event:full_reload',**kw):
 e=dict(name=name,source='스킬1',type=kind,stat=stat,target=target or ['self']*21,trigger=dict(timing=[timing],condition=[]))
 if value is not None:e['fixed_value']=value
 if kind=='buff':e.update(duration=-1,max_stack=1)
 e.update(kw);return e
notify=lambda t=0,event=19:[t,0,event,0,0,-1,0,0]
query=lambda t=.1,index=0:[t,2,0,0,0,index,0,0]
rows=[]
def add(name,effects,script=None,allies=None,owners=None,combat=None,weapon=False):
 row=dict(instant_list_reference=True,name='instant-list-'+name,effects=effects,script=script or [notify(),query()],expected_queries=[dict(time=x[0]) for x in (script or [notify(),query()]) if x[1]==2])
 if combat:row.update(combat=combat,instant_list_weapon_observer=weapon)
 else:row['environment']=dict(allies=allies or [dict(base_hp=1000,hp=100,base_cover_hp=1000,cover_hp=100) for _ in range(5)])
 if owners:row['owners']=owners
 rows.append(row)
for count in (1,5,10,11,21):
 add('heal-'+str(count),[effect('heal','heal_hp_pct',target=['self']*count)])
 add('reduce-'+str(count),[effect('reduce','current_hp_reduce',10,target=['self']*count)])
add('nested-heal-order',[effect('heal','heal_hp_pct',target=[['self','allies_right:1'],['self']])])
add('rank-frozen-before-first-delivery',[effect('heal','heal_hp_pct',40,target=['allies_lowest_hp:1','self','allies_lowest_hp:1'])],allies=[dict(base_hp=1000,hp=x) for x in (100,200,300,400,500)])
add('heal-zero-still-notifies',[effect('heal','heal_hp_pct',0),effect('seen','atk_pct',10,target='self',kind='buff',timing='event:heal_received',max_stack=100)])
add('heal-full-still-notifies',[effect('heal','heal_hp_pct',100),effect('seen','atk_pct',10,target='self',kind='buff',timing='event:heal_received',max_stack=100)])
add('heal-live-caster-basis-between-children',[effect('heal','heal_hp_pct',10,scaling='max_hp'),effect('grow','max_hp_pct',10,target='self',kind='buff',timing='event:heal_received',max_stack=100)])
add('cover-live-caster-basis-between-children',[effect('heal','cover_heal_pct',1,scaling='max_hp'),effect('grow','max_hp_pct',10,target='self',kind='buff',timing='event:cover_healed',max_stack=100)])
for stat in ('cover_heal_pct','cover_revive'):
 for current in (0,100,1000):add(stat+'-'+str(current),[effect('cover',stat,10),effect('seen','atk_pct',10,target='self',kind='buff',timing='event:cover_healed',max_stack=100)],allies=[dict(base_hp=1000,base_cover_hp=1000,cover_hp=current) for _ in range(5)])
for current in (0,1000):add('cover-zero-'+str(current),[effect('cover','cover_heal_pct',0),effect('seen','atk_pct',10,target='self',kind='buff',timing='event:cover_healed',max_stack=100)],allies=[dict(base_hp=1000,base_cover_hp=1000,cover_hp=current) for _ in range(5)])
for stat,heal in (('shield_from_max_hp_pct','shield_heal_pct'),('decoy','decoy_heal_pct')):
 for scaling in (None,'max_hp'):
  effects=[effect('guard',stat,20,target='self',kind='buff',timing='on_attack'),effect('heal',heal,1,**(dict(scaling=scaling) if scaling else {}))]
  add(stat+'-heal-'+str(scaling),effects,[notify(0,7),[.1,31,0,0,1,-1,100,100],notify(.2),query(.3)])
 add(stat+'-absent-heal',[effect('heal',heal,100)])
base=json.loads((R/'tests/fixtures/portable-ammo-instants.json').read_text())['cases'][0]
for stat,value in (('ammo_charge_pct',-10),('ammo_charge_pct',0),('ammo_charge_flat',-1),('ammo_charge_flat',-.9),('ammo_charge_flat',1)):
 combat=copy.deepcopy(base['combat'])
 for w in combat['weapons']:w.update(enabled=False,capacity=100)
 effects=[copy.deepcopy(base['effects'][0]),effect('ammo',stat,value,timing='event:cover_healed'),effect('seen','atk_pct',10,target='self',kind='buff',timing='event:ammo',max_stack=100)]
 add(stat+'-'+str(value),effects,[[0,4,0,0,0,-1,0,0],notify(.1,17),query(.1)],combat=combat,weapon=True)
combat=copy.deepcopy(base['combat']);combat['weapons'][0].update(enabled=True,capacity=2,interval=.1,reload=3,reload_cancel_on_full=True)
add('ammo-cancel-reload-after-second-recipient',[copy.deepcopy(base['effects'][0]),effect('ammo','ammo_charge_pct',50,timing='event:cover_healed')],[[.12,24,0,0,0,-1,0,0],notify(.2,17),query(.2)],combat=combat,weapon=True)
for stat in ('ammo_charge_pct','burst_charge_pct'):
 combat=copy.deepcopy(base['combat'])
 for w in combat['weapons']:w.update(enabled=False,stage=0)
 effects=[copy.deepcopy(base['effects'][0]),effect('ammo',stat,10,target=['allies_with_buff:absent'],timing='event:cover_healed'),effect('seen','atk_pct',10,target='self',kind='buff',timing='event:ammo',max_stack=100)]
 add(stat+'-empty-members',effects,[[0,4,0,0,0,-1,0,0],notify(.1,17),query(.1)],combat=combat,weapon=True)
for count in (2,21):
 combat=copy.deepcopy(base['combat'])
 for w in combat['weapons']:w.update(enabled=False,stage=0)
 add('shared-gauge-once-'+str(count),[effect('gauge','burst_charge_pct',10,target=['self']*count)],[[0,4,0,0,0,-1,0,0],notify(.1),query(.1)],combat=combat)
for count in (2,21):
 combat=dict(weapons=[dict(enabled=False,stage=s,cooldown=20,capacity=100) for s in (1,2,3,0,0)],targets=[dict(hp=1e30)],initial_gauge=100,trace='full')
 add('cooldown-'+str(count),[effect('cd','burst_cooldown_reduce',1,target=['self']*count)],[[0,4,0,0,0,-1,0,0],notify(.1),query(.1)],combat=combat)
add('cover-overflow-clamps-finite',[effect('cover','cover_heal_pct',1e308)])
add('periodic-heal-keeps-all-deliveries',[effect('heal','heal_hp_pct',1,duration=.2,tick_interval=.1)],[notify(),query(0,0),query(.1,1),query(.2,2)])
add('periodic-shield-heal-keeps-all-deliveries',[effect('guard','shield_from_max_hp_pct',50,target='self',kind='buff',timing='on_attack'),effect('heal','shield_heal_pct',1,duration=.3,tick_interval=.1)],[notify(0,7),[.01,31,0,0,1,-1,400,100],notify(.1),query(.1,0),query(.2,1),query(.3,2)])
(R/'tests/fixtures/portable-instant-lists.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n');print(len(rows))
