"""Authored global-code conditions, with independent native checks after GPU readback."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];rows=[]
codes=['작열','수냉','풍압','전격','철갑','','unknown:code',' 전격 ']
def effect(name='gate',stat='atk_pct',target='self',timing='on_attack',conditions=(),duration=-1,value=10,**kw):
    row=dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target=target,duration=duration,max_stack=1,trigger=dict(timing=[timing],condition=list(conditions)))
    row.update(kw);return row
def notify(t=0,event=7,owner=0):return [t,0,event,owner,0,-1,0,0]
def query(t=0,index=0,target=0):return [t,2,0,0,target,index,0,0]
def add(name,effects,world=None,script=None,owners=None,expected=None,combat=None):
    script=script or [notify(),query(.1)]
    row=dict(name='enemy-code-'+name,code_reference=True,effects=effects,script=script,expected_queries=expected or [{} for c in script if c[1]==2],environment=dict(enemy_code=world,allies=[dict(base_hp=1000,hp=100) for _ in range(5)]))
    if owners is not None:row['owners']=owners
    if combat is not None:row['combat']=combat;row['code_enemy_reference']=True
    rows.append(row)
for w,world in enumerate([None]+codes):
    for p,predicate in enumerate(codes):
        add('matrix-'+str(w)+'-'+str(p),[effect(conditions=['target_code:'+predicate])],world,expected=[dict(attack_buffs=[10 if not world or world==predicate else 0,0,0,0,0])])
for owner in range(5):
    for match in (True,False):
        add('owner-'+str(owner)+'-'+str(match),[effect(target='all_allies',conditions=['target_code:전격'])],world='전격' if match else '풍압',script=[notify(owner=owner),query(.1)],owners=[owner],expected=[dict(attack_buffs=[10 if match else 0]*5)])
for timing in ('passive','on_attack'):
    for duration in (-1,1):
        for match in (True,False):
            add(timing+'-'+str(duration)+'-'+str(match),[effect(timing=timing,duration=duration,conditions=['target_code:전격'])],world='전격' if match else '풍압',script=[notify(event=0),notify(),query(.1),query(1,1)],expected=[dict(attack_buffs=[10 if match else 0,0,0,0,0]),dict(attack_buffs=[10 if match and (duration==-1 or timing=='passive') else 0,0,0,0,0])])
for match in (True,False):
    marker=effect('live:state',stat='',duration=.5)
    gate=effect(timing='passive',conditions=['target_code:전격','self_state:live:state'])
    add('code-and-live-state-'+str(match),[marker,gate],world='전격' if match else '풍압',script=[notify(event=0),query(),notify(.1),query(.1,1),query(.6,2)],expected=[dict(attack_buffs=[0]*5),dict(attack_buffs=[10 if match else 0,0,0,0,0]),dict(attack_buffs=[0]*5)])
for third in ('전격','풍압'):
    add('three-slots-'+third,[effect(conditions=['target_code:전격','target_code:전격','target_code:'+third])],world='전격',expected=[dict(attack_buffs=[10 if third=='전격' else 0,0,0,0,0])])
for world in (None,'전격','풍압'):
    heal=dict(name='heal',source='스킬1',type='instant',stat='heal_hp_pct',fixed_value=10,target='all_allies',trigger=dict(timing=['on_attack'],condition=['target_code:전격']))
    add('instant-'+str(world),[heal],world,expected=[dict(allies=[dict(hp=200 if world!='풍압' else 100) for _ in range(5)])])
add('label-collision',[effect(conditions=['target_code:gate'])],world='gate',expected=[dict(attack_buffs=[10,0,0,0,0])])

combat=dict(weapons=[dict(enabled=False) for _ in range(5)],targets=[dict(hp=1e8,defense=400),dict(hp=1000,kind=5,identity=0)])
for world in ('전격','풍압'):
    for predicate in ('전격','풍압'):
        add('global-context-'+world+'-'+predicate,[effect(stat='def_pct',target='target',timing='hit_count',value=-25,conditions=['target_code:'+predicate])],world,
            script=[[0,4,0,0,0,-1,0,0],[.1,20,0,0,1,-1,0,0],notify(.1,8),query(.1,0,0),query(.1,1,1)],combat=copy.deepcopy(combat),expected=[dict(enemy_modifiers=dict(defense_pct=0)),dict(enemy_modifiers=dict(defense_pct=-25 if world==predicate else 0))])
add('global-code-and-add-context',[effect(stat='def_pct',target='target',timing='hit_count',value=-25,conditions=['target_code:전격','target_is_add'])],world='전격',script=[[0,4,0,0,0,-1,0,0],notify(.1,8),[.2,20,0,0,1,-1,0,0],notify(.2,8),query(.2,0,0),query(.2,1,1)],combat=copy.deepcopy(combat),expected=[dict(enemy_modifiers=dict(defense_pct=0)),dict(enemy_modifiers=dict(defense_pct=-25))])
(R/'tests/fixtures/portable-enemy-codes.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n');print(len(rows))
