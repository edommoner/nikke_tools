"""Authored full native battles shared with the forthcoming GPU landing bridge."""
import copy
from target_counter_cases import marker


def fixtures(stack):
    base=copy.deepcopy(stack.fixtures()[0]);base.update(observe_target_counters=True,observe_enemy_fields=False,observe_named_state=False,observe_actor_pools=True,state_queries=[],field_queries=[],base_atk=[1000,0,0,0,0],duration=.05)
    def effect(stat,value,name,kind='buff',timing='battle_start'):
        e=dict(type=kind,name=name,source='스킬1',stat=stat,fixed_value=value,target='self',trigger=dict(timing=[timing],condition=[]))
        if kind=='buff':e['duration']=-1
        return e
    rows=[]
    for kind,patterns in [('body',[dict(id='idle',kind='idle')]),('add',[dict(id='wave',kind='summon',spec=dict(count=1,hp=50))]),('add-survives',[dict(id='wave',kind='summon',spec=dict(count=1,hp=100000))]),('add-hit-hp',[dict(id='wave',kind='summon',spec=dict(count=1,hit_hp=2))])]:
        c=copy.deepcopy(base);counter=marker(threshold=1,attackers='owner',actor=dict(kind='body' if kind=='body' else 'add',identity=0,generation=1));counter['target']='boss';counter['trigger']['timing']=['battle_start']
        c.update(name=kind+'-completion-versus-lifesteal-order',patterns=patterns,effects=[effect('current_hp_reduce',50,'wound','instant'),effect('lifesteal_pct',10,'leech'),counter,effect('lifesteal_pct',40,'surge',timing='event:target_counter_complete:marker')],owners=[0,0,0,0]);rows.append(c)
    for original in list(rows[:3]):
        c=copy.deepcopy(original);c['name']='zero-base-attack-'+c['name'];c['base_atk'][0]=0;rows.append(c)
    for original in list(rows[:3]):
        c=copy.deepcopy(original);c['name']='second-hit-'+c['name'];c['effects'][2]['target_counter']['threshold']=2;c['duration']=.15;rows.append(c)
    for hp in (50,100000):
        c=copy.deepcopy(rows[0]);c['name']='part-'+str(hp)+'-completion-versus-lifesteal-order'
        c['patterns']=[dict(id='parts',kind='parts',targets=[dict(name='right',hp=hp,reach=1)])]
        c['effects'][2]['target_counter']['actor']['kind']='part'
        c['effects'].insert(2,effect('pierce_enabled',1,'pierce'));c['owners'].insert(2,0);rows.append(c)
    c=copy.deepcopy(rows[1]);c['name']='fatal-add-cancels-without-reward';c['effects'][2]['target_counter'].update(threshold=100,on_death=False);rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='expires-before-second-physical-shot';c['duration']=.15;c['effects'][2].update(duration=.05);c['effects'][2]['target_counter']['threshold']=100;rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='stale-body-generation-does-not-alias-live-body';c['effects'][2]['target_counter']['actor']['generation']=2;rows.append(c)
    c=copy.deepcopy(rows[2]);c['name']='unknown-add-identity-does-not-alias-first-add';c['effects'][2]['target_counter']['actor']['identity']=1;rows.append(c)
    c=copy.deepcopy(rows[1]);c['name']='nonowner-fatal-add-death-still-completes';c['owners'][2:4]=[1,1];rows.append(c)
    for kind in ('vanish','shield'):
        c=copy.deepcopy(rows[0]);c['name']=kind+'-does-not-synthesize-blocked-impact'
        c['patterns']=[dict(id='barrier',kind=kind,until={'time':.1},**({'code':'수냉'} if kind=='shield' else {}))]
        c['effects'][2]['target_counter']['outcomes']=['blocked'];rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='shotgun-three-pellets-credit-second-before-heal';c['combat']['weapons'][0].update(base_weapon_type='SG',pellets=3);c['effects'][2]['target_counter']['threshold']=2;rows.append(c)
    for pellets,family in [(1,'skill'),(3,'weapon')]:
        c=copy.deepcopy(rows[0]);c['name']='skill-mode-'+str(pellets)+'-pellets-credit-family-'+family
        mode=dict(name='counter-mode',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=100,max_ammo=-1,fire_rate=10,fire_rate_max=10,charge=False,pellets=pellets,muzzles=1,post_fire_delay=0,burst_energy=.25,core_dmg_mult=200,target='self',duration=.3,skill_damage=True,trigger=dict(timing=['battle_start'],condition=[]))
        c['effects'][2]['target_counter'].update(threshold=1 if pellets==1 else 2,families=[family]);c['effects'].insert(2,mode);c['owners'].insert(2,0);rows.append(c)
    c=copy.deepcopy(rows[-2]);c['name']='skill-mode-single-physical-weapon-family-positive';c['effects'][3]['target_counter']['families']=['weapon'];rows.append(c)
    return rows
