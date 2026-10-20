"""Literal named-state inputs; no native states or quantities become GPU input."""
import copy, json
from pathlib import Path
R = Path(__file__).resolve().parents[1]
rows = []
def effect(name, stat=None, target='self', timing='on_attack', conditions=(), **kw):
    e = dict(name=name, source='스킬1', type='buff', stat=stat, target=target,
             duration=.5, max_stack=1, trigger=dict(timing=[timing], condition=list(conditions)))
    if stat is not None: e['fixed_value'] = 10
    e.update(kw); return e
def notify(t=0, event=7, owner=0): return [t,0,event,owner,0,-1,0,0]
def query(t, i): return [t,2,0,0,0,i,0,0]
def add(name, effects, script=None, owners=None):
    script = script or [notify(),notify(.1,19),query(.1,0),query(.5,1)]
    row = dict(name='named-state-'+name, named_state_reference=True, effects=effects,
               script=script, expected_queries=[dict(time=c[0]) for c in script if c[1]==2],
               environment=dict(allies=[dict(base_hp=1000) for _ in range(5)]))
    if owners is not None: row['owners'] = owners
    rows.append(row)

names = ['바니 모드 : 인게이지','바니 모드 : 스탠스','무대 파트 : 보컬','무대 파트 : 댄스',
         '状態:α:β','A::B',' spaced : name ','A:\nB']
for i, name in enumerate(names):
    add(str(i)+'-self-live-expiry', [effect(name),effect('gate','atk_pct',timing='event:full_reload',conditions=['self_state:'+name],duration=-1)])
    add(str(i)+'-negative-activation', [effect(name,timing='hit_count'),effect('gate','atk_pct',timing='event:full_reload',conditions=['not_self_state:'+name],duration=-1)],
        [notify(0,19),query(0,0),notify(.1,8),query(.1,1),query(.6,2)])
    add(str(i)+'-apply-and-end', [effect(name),effect('applied','atk_pct',timing='event:'+name,duration=2),effect('ended','atk_pct',timing='event:state_end:'+name,duration=2)],
        [notify(),query(0,0),query(.5,1)])

name = names[0]
add('finite-gate-keeps-duration-after-state-expiry',[effect(name),effect('gate','atk_pct',timing='event:full_reload',conditions=['self_state:'+name],duration=2)])
for target, owners, label in [('self',[1,0],'other-caster-other-recipient'),('allies_adjacent:1',[1,0],'other-caster-self-recipient'),('allies_right:1',[0,0],'own-caster-other-recipient')]:
    add(label,[effect(name,target=target),effect('gate','atk_pct',target='all_allies',timing='event:full_reload',conditions=['self_state:'+name],duration=-1)],
        [notify(0,7,owners[0]),notify(.1,19),query(.1,0)],owners)
add('query-recipient-is-not-condition-owner',[effect(name),effect('gate','atk_pct',target='allies_right:1',timing='event:full_reload',conditions=['self_state:'+name],duration=-1)])
add('spaces-are-distinct',[effect(name),effect('gate','atk_pct',timing='event:full_reload',conditions=['self_state:'+name.replace(' : ',':')],duration=2)])
add('prefixes-are-distinct',[effect('A:B'),effect('gate','atk_pct',timing='event:full_reload',conditions=['self_state:A'],duration=2)])
add('unnamed-state-retains-empty-mode-rule',[effect('ordinary'),effect('gate','atk_pct',timing='event:full_reload',conditions=['self_state:'],duration=2)])
add('two-different-colon-states',[effect('A:B'),effect('A:C',timing='hit_count'),effect('gate','atk_pct',timing='event:full_reload',conditions=['self_state:A:B','not_self_state:A:C'],duration=-1)],
    [notify(),notify(.1,19),query(.1,0),notify(.2,8),query(.2,1)])
for scope in ('recipients',None):
    kw = dict(event_scope=scope) if scope else {}
    effects=[effect(name,target=['self','allies_right:1','self'],**kw)]
    effects += [effect('receiver '+str(i),'atk_pct',timing='event:'+name,duration=2,max_stack=10) for i in range(2)]
    add('ordered-notices-'+str(scope),effects,[notify(),query(0,0)],owners=[0,0,1])

for stat in ('dot_dmg_pct','split_dmg_pct'):
    add('stat-applied-'+stat,[effect('modifier:'+stat,stat,target=['self','self','allies_right:1']),effect('seen0','atk_pct',timing='event:stat_applied:'+stat,duration=2,max_stack=10),effect('seen1','atk_pct',timing='event:stat_applied:'+stat,duration=2,max_stack=10)],[notify(),query(0,0)],owners=[0,0,1])

for stat in ('dot_dmg_pct','split_dmg_pct'):
    timing='event:stat_applied:'+stat
    observer=effect('seen','atk_pct',timing=timing,duration=2,max_stack=100)
    for count in (1,11,21):
        add('stat-'+stat+'-order-'+str(count),[effect('mod:'+stat,stat,target=['self']*count),copy.deepcopy(observer)],[notify(),query(0,0)])
    add('stat-'+stat+'-refresh-max-one',[effect('mod:'+stat,stat),copy.deepcopy(observer)],[notify(),notify(.1),query(.1,0)])
    add('stat-'+stat+'-unnamed',[effect('',stat),copy.deepcopy(observer)],[notify(),query(0,0)])
    add('stat-'+stat+'-lazy-stays-unresolved',[effect('mod:'+stat,stat,target='allies_top_atk:1'),copy.deepcopy(observer)],[notify(),query(0,0)])
    removal=dict(name='remove',source='스킬1',type='instant',stat='remove_named_buff',target='self',target_effect='mod:'+stat,trigger=dict(timing=['event:mod:'+stat],condition=[]))
    add('stat-'+stat+'-named-child-removes-parent',[effect('mod:'+stat,stat,target=['self']*21),removal,copy.deepcopy(observer)],[notify(),query(0,0)])

for stat in ('dot_dmg_pct','split_dmg_pct'):
    c=copy.deepcopy(next(c for c in rows if c['name']=='named-state-stat-'+stat+'-refresh-max-one'))
    parent=c['effects'][0];parent['target']='allies_top_atk:1'
    other=copy.deepcopy(parent);other['target']='self';other['trigger']['timing']=['event:full_reload'];c['effects'].insert(1,other)
    c['name']='named-state-alias-resolved-lazy-to-eager-'+stat
    c['script']=[notify(),query(0,0),notify(.1,19),query(.1,1)];c['expected_queries']=[dict(time=0),dict(time=.1)];rows.append(c)

for base_type,mode,value in [('RL','charge',50),('SR','charge',50),('AR','charge',50),('RL','auto',50),('RL','charge',-50),('RL','charge',0)]:
    name='named-state-base-'+base_type+'-'+mode+'-'+str(value)
    effects=[effect('stage:voice','',timing='battle_start',duration=-1),effect('explosion:bonus','projectile_explosion_dmg_pct',timing='battle_start',conditions=['self_state:stage:voice'],fixed_value=value,duration=-1),effect('no critical','crit_rate',target='all_allies',timing='battle_start',fixed_value=-15,duration=-1)]
    weapons=[dict(enabled=i==0,base_weapon_type=base_type if i==0 else 'AR',mode=mode if i==0 else 'auto',capacity=10,interval=1,charge=.5,full_charge_mult=100) for i in range(5)]
    rows.append(dict(name=name,named_state_reference=True,mode_session_reference=True,effects=effects,combat=dict(weapons=weapons,targets=[dict(hp=1e30)]),script=[[.5,24,0,0,0,-1,0,0],[.5,2,0,0,0,0,0,0]],expected_queries=[dict(damage=[1000*(1+value/100) if base_type=='RL' and mode=='charge' else 1000])]))
for replacement in ('AR','SR'):
    c=copy.deepcopy(next(c for c in rows if c['name']=='named-state-base-RL-charge-50'))
    c['name']='named-state-base-RL-mode-'+replacement
    mode=dict(name='changed:weapon',source='스킬2',type='weapon_change',weapon_type=replacement,damage_coeff=100,max_ammo=10,fire_rate=1,fire_rate_max=1,charge=replacement=='SR',pellets=1,muzzles=1,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,reload_time=1,duration=2,target='self',trigger=dict(timing=['event:cover_healed'],condition=[]))
    if replacement=='SR':mode.update(charge_time=.5,full_charge_mult=100)
    c['effects'].append(mode);c['script']=[[0,24,0,0,0,-1,0,0],notify(.1,17),[1,24,0,0,0,-1,0,0],query(1,0)];c['expected_queries']=[dict(attack_buffs=[0]*5)];rows.append(c)

# Existing authored weapon scenarios exercise the actual native controller.
source=json.loads((R/'tests/fixtures/portable-mode-sessions.json').read_text())['cases']
for title in ('mode-entry-state-is-installed-before-notice','mode-entry-is-squad-broadcast','mode-toggle-exit-does-not-emit-entry','mode-nested-entry-finishes-before-parent-resumes'):
    c=copy.deepcopy(next(c for c in source if c['name']==title))
    def rename(x):
        if isinstance(x,str): return x.replace('Mode A',name).replace('Mode B','状態:β')
        if isinstance(x,list): return [rename(v) for v in x]
        if isinstance(x,dict): return {k:rename(v) for k,v in x.items()}
        return x
    c=rename(c);c['name']='named-state-'+title;c['named_state_reference']=True;rows.append(c)

(R/'tests/fixtures/portable-named-states.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n')
print(len(rows))
