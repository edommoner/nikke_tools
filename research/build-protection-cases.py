"""Literal public stimuli; native observations never become GPU inputs."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def buff(name,stat,value=10,*,target='self',duration=-1,timing='on_attack',condition=(),**extra):
 e=dict(name=name,source='스킬1',type='buff',stat=stat,target=target,duration=duration,max_stack=1,trigger=dict(timing=[timing],condition=list(condition)))
 e.update(extra)
 if value is not None:e['fixed_value']=value
 return e
def instant(name,stat,value=10,**extra):return dict(buff(name,stat,value,**extra),type='instant')
def notify(t=0,event=7,owner=0):return [t,0,event,owner,0,-1,0,0]
def hit(t=.1,amount=150,mask=1,*,pierce=False,covered=0):return [t,31,int(pierce),covered,mask,-1,amount,100]
def query(t=.2,index=0):return [t,2,0,0,0,index,0,0]
rows=[]
def add(name,effects,script,owners=None,allies=None):
 rows.append(dict(protection_reference=True,name='protection-'+name,effects=effects,script=script,expected_queries=[dict(time=c[0]) for c in script if c[1]==2],environment=dict(allies=allies or [dict(base_hp=1000+i*1000,base_cover_hp=200,cover_hp=200) for i in range(5)]),**(dict(owners=owners) if owners else {})))
for stat in ('shield_from_max_hp_pct','shared_shield_from_max_hp_pct','decoy'):
 for pierce in (False,True):
  for covered in (0,1):add(stat+'-pierce-'+str(pierce)+'-cover-'+str(covered),[buff('guard',stat,10)],[notify(),query(0,0),hit(.1,150,pierce=pierce,covered=covered),query(.1,1),hit(.2,150,pierce=pierce,covered=covered),query(.2,2)])
for stat in ('shield_from_max_hp_pct','decoy'):
 add(stat+'-all-caster-snapshot',[buff('hp','max_hp_pct',50),buff('guard',stat,10,target='all_allies')],[notify(),query(0,0),hit(.1,50,mask=31),query(.1,1)])
 add(stat+'-heal',[buff('guard',stat,50),instant('heal','shield_heal_pct' if stat.startswith('shield') else 'decoy_heal_pct',10,timing='event:full_reload')],[notify(),hit(.1,100),notify(.2,19),query(.2)])
 add(stat+'-heal-caster',[buff('guard',stat,50,target='all_allies'),instant('heal','shield_heal_pct' if stat.startswith('shield') else 'decoy_heal_pct',10,target='all_allies',scaling='max_hp',timing='event:full_reload')],[notify(),hit(.1,100,31),notify(.2,19),query(.2)])
 add(stat+'-two-layers',[buff('old',stat,10),buff('new',stat,20,timing='event:full_reload')],[notify(),notify(.1,19),hit(.2,250),query(.2,0),hit(.3,250),query(.3,1)])
 add(stat+'-refresh-order',[buff('old',stat,10),buff('new',stat,20,timing='event:full_reload')],[notify(),notify(.1,19),notify(.2),hit(.3,150),query(.3)])
 add(stat+'-negative',[buff('guard',stat,-10)],[notify(),query(0),hit(.1),query(.1,1)])
 add(stat+'-missing-value',[buff('guard',stat,None)],[notify(),query(0),hit(.1),query(.1,1)])
 add(stat+'-heal-no-resurrection',[buff('guard',stat,10),instant('heal','shield_heal_pct' if stat.startswith('shield') else 'decoy_heal_pct',100,timing='event:full_reload')],[notify(),hit(.1),notify(.2,19),query(.2)])
 add(stat+'-expired',[buff('guard',stat,10,duration=.1)],[notify(),hit(.1),query(.1)])
add('amp-multiple-and-partial',[buff('amp','next_shield_hp_pct',50,target='all_allies'),buff('amp2','next_shield_hp_pct',25,target='all_allies'),buff('guard','shield_from_max_hp_pct',10,timing='event:full_reload')],[notify(),notify(.1,19),query(.1)])
add('shield-invincible-caster',[buff('guard','shield_from_max_hp_pct',10,target='all_allies'),buff('immortal','shield_invincible',None)],[notify(),hit(.1,150,31,pierce=True),query(.1)])
add('shield-invincible-recipient-is-not-caster',[buff('guard','shield_from_max_hp_pct',10,target='all_allies'),buff('immortal','shield_invincible',None)],[notify(),notify(0,7,1),hit(.1,150,31,pierce=True),query(.1)],owners=[0,1])
add('layer-shield-decoy',[buff('shield','shield_from_max_hp_pct',10),buff('decoy','decoy',10)],[notify(),hit(.1),query(.1,0),hit(.2),query(.2,1),hit(.3),query(.3,2)])
add('pierce-all-shields',[buff('one','shield_from_max_hp_pct',10),buff('two','shield_from_max_hp_pct',20)],[notify(),hit(.1,150,pierce=True),query(.1)])
add('cover-disabled',[buff('decoy','decoy',10),buff('blocked','cover_disabled',None)],[notify(),hit(.1,150,covered=1),query(.1)])
add('during-shield',[buff('shield','shield_from_max_hp_pct',10),buff('boost','atk_pct',50,timing='passive',condition=['during_shield'])],[notify(0,0),notify(.1),query(.1,0),hit(.2),query(.2,1)])
add('consumed-lifetime',[buff('shield','shield_from_max_hp_pct',10,end_on_shield_consumed=True),buff('ended','atk_pct',23,timing='event:state_end:shield')],[notify(),hit(.1),query(.1)])
add('consumed-multiple-recipient',[buff('shield','shield_from_max_hp_pct',10,target='all_allies',end_on_shield_consumed=True),buff('ended','atk_pct',23,timing='event:state_end:shield')],[notify(),hit(.1,200,1),query(.1,0),hit(.2,200,30),query(.2,1)])
add('applied-after-all-snapshots',[buff('shield','shield_from_max_hp_pct',10,target='all_allies'),buff('boost','max_hp_pct',100,timing='event:shield_applied')],[notify(),query(0)])
add('amp-silent-no-state-end',[buff('amp','next_shield_hp_pct',50),buff('shield','shield_from_max_hp_pct',10,timing='event:full_reload'),buff('end','atk_pct',99,timing='event:state_end:amp')],[notify(),notify(.1,19),query(.1)])
add('consumed-refresh-still-ends',[buff('shield','shield_from_max_hp_pct',10,timing='event:shield_consumed',end_on_shield_consumed=True),buff('initial','shield_from_max_hp_pct',10),buff('ended','atk_pct',23,timing='event:state_end:shield')],[notify(),notify(.05,43),hit(.1,150),query(.1)])
add('consumed-child-replace-other-shield',[buff('old','shield_from_max_hp_pct',10),buff('later','shield_from_max_hp_pct',20),instant('remove','remove_named_buff',0,target_effect='old',timing='event:shield_consumed'),buff('replacement','shield_from_max_hp_pct',40,timing='event:shield_consumed')],[notify(),hit(.1,250,pierce=True),query(.1)])
old=buff('old','shield_from_max_hp_pct',10,end_on_shield_consumed=True);old['trigger']['timing']=['on_attack','event:shield_consumed']
add('captured-object-survives-carrier-reuse',[instant('remove','remove_named_buff',0,target_effect='old',timing='event:shield_consumed'),old,buff('later','shield_from_max_hp_pct',20,end_on_shield_consumed=True)],[notify(),hit(.1,250,pierce=True),query(.1)])
add('nonzero-caster-invincible',[buff('guard','shield_from_max_hp_pct',10,target='all_allies'),buff('immunity','shield_invincible',None)],[notify(0,7,2),hit(.1,500,31,pierce=True),query(.1)],owners=[2,2])
add('partial-removal-keeps-resource-maps',[buff('guard','shield_from_max_hp_pct',10,target='all_allies'),instant('remove','remove_named_buff',0,target_effect='guard',remove_scope='target',timing='event:full_reload')],[notify(),notify(.1,19),hit(.2,150,1),query(.2)])
add('amp-partial-maps',[buff('amp','next_shield_hp_pct',50,target='all_allies'),buff('own','shield_from_max_hp_pct',10,timing='event:full_reload'),buff('squad','shield_from_max_hp_pct',10,target='all_allies',timing='hit_count')],[notify(),notify(.1,19),notify(.2,8),query(.2)])
for stat in ('shield_from_max_hp_pct','decoy'):
 heal=instant('periodic-heal','shield_heal_pct' if stat.startswith('shield') else 'decoy_heal_pct',10,timing='event:full_reload',duration=1,tick_interval=.2,scaling='max_hp')
 add(stat+'-periodic-heal',[buff('guard',stat,50),heal],[notify(),hit(.1,200),notify(.15,19),query(.15,0),query(.35,1),query(.55,2)])
add('refresh-observes-old-shield-when-snapshotting',[buff('guard','shield_from_max_hp_pct',10),buff('conditional-hp','max_hp_only_pct',100,timing='passive',condition=['during_shield'])],[notify(0,0),query(0,0),notify(.1),query(.1,1),notify(.2),query(.2,2)])
add('refresh-observes-old-shield-for-amp',[buff('guard','shield_from_max_hp_pct',10),buff('conditional-amp','next_shield_hp_pct',50,timing='event:full_reload',condition=['during_shield'])],[notify(),notify(.1,19),notify(.2),query(.2)])
add('all-256-shield-definitions',[buff('guard-'+str(i),'shield_from_max_hp_pct',10,end_on_shield_consumed=True) for i in range(256)],[notify(),hit(.1,150,pierce=True),query(.1)])
for max_stack in (1,2):
 a=buff('same','shield_from_max_hp_pct',10,max_stack=max_stack)
 b=buff('same','shield_from_max_hp_pct',40,timing='event:full_reload',max_stack=max_stack);b['source']='스킬2'
 add('alias-refresh-keeps-first-definition-'+str(max_stack),[a,b,buff('applied','atk_pct',23,timing='event:shield_applied',max_stack=10)],[notify(),notify(.1,19),query(.1)])
add('canceled-before-resource-construction',[buff('guard','shield_from_max_hp_pct',10),instant('cancel','remove_named_buff',0,target_effect='guard',timing='event:guard'),buff('applied','atk_pct',23,timing='event:shield_applied')],[notify(),query(0)])
guard=buff('guard','shield_from_max_hp_pct',10);guard['source']='스킬2'
add('recreated-during-named-callback',[guard,instant('cancel','remove_named_buff',0,target_effect='guard',timing='event:guard',max_trigger=1),instant('again','force_skill_use',0,target_skill='스킬2',timing='event:guard',max_trigger=1),buff('applied','atk_pct',23,timing='event:shield_applied',max_stack=10)],[notify(),query(0)])
add('stack-initialization-has-no-resource-snapshot',[buff('guard','shield_from_max_hp_pct',10,duration=.05),instant('init','buff_stack_init',2,target_effect='guard',timing='event:full_reload')],[notify(),notify(.1,19),hit(.11),query(.11)])
(R/'tests/fixtures/portable-protection.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n');print('Authored protection cases',len(rows))
