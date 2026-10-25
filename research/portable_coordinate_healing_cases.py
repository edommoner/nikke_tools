"""Literal healing/storage compositions; never compute a CPU battle schedule."""
import copy
from portable_coordinate_sampled_vital_cases import fixtures as vital
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    rows=[];seeds=vital();base=seeds[0]
    def add(label):
        c=copy.deepcopy(base);c.update(name='coordinate-healing/'+label,duration=.95,seed=1701+len(rows),effects=[],owners=[],observe_healing_storage=True,coordinate_healing=True)
        rows.append(c);return c
    def effect(c,e,owner=0):c['effects'].append(e);c['owners'].append(owner);return e
    def pool(c,**kw):
        e=field('heal_overcharge_store_atk_pct',150,'self','pool',duration=.4);e.update(kw);return effect(c,e)
    def release(c,**kw):
        e=instant('heal_overcharge_discharge',0,'all_allies','release','event:state_end:pool');e['target_effect']='pool';e.update(kw);return effect(c,e)
    def heal(c,amount=10,target='self',timing='battle_start',**kw):
        e=instant('heal_hp_pct',amount,target,'deposit',timing);e.update(kw);return effect(c,e)
    def store(c,**kw):
        e=field('heal_overcharge_store',20,'all_allies','hp-store');e.update(kw);return effect(c,e)
    def drain(c):effect(c,instant('current_hp_reduce',50,'all_allies','drain'))
    def attack(c):c['patterns'].append(dict(id='incoming',kind='attack',delay=.55,spec=dict(atk=1300,coeff=100,target='all',hits=2,interval=.15,pierce=True)))
    c=add('pool-discharge');drain(c);pool(c);heal(c,100);release(c)
    c=add('pool-empty');pool(c);release(c)
    c=add('hp-store-overheal');store(c);heal(c,40,target='all_allies');attack(c)
    c=add('hp-store-expiry');store(c,duration=.3);heal(c,40,target='all_allies');attack(c)
    c=add('pool-and-hp-store');store(c);pool(c);heal(c,100);release(c);attack(c)
    c=add('share-deposits');drain(c);pool(c);effect(c,field('heal_split',50,'all_allies','share'));heal(c,20);release(c)
    c=add('periodic-deposits');pool(c);heal(c,20,duration=.3,tick_interval=.1);release(c)
    c=add('lifesteal-deposits');pool(c);effect(c,field('lifesteal_pct',100,'self','life'));release(c)
    c=add('pool-live-capacity');pool(c);effect(c,field('accumulate_max_scale_pct',100,'self','larger',target_effect='pool'));heal(c,100);release(c)
    c=add('mode-shotgun-store');store(c);pool(c);effect(c,copy.deepcopy(next(e for e in seeds[2]['effects'] if e['type']=='weapon_change')));effect(c,field('lifesteal_pct',100,'self','life'));release(c)
    c=add('cover-repair-no-deposit');pool(c);effect(c,instant('cover_heal_pct',100,'self','repair'));release(c)
    c=add('release-one-shot');drain(c);pool(c);heal(c,100);release(c,trigger=dict(timing=['every:0.2s'],condition=[]),max_trigger=3)
    c=add('mode-cover-pool');pool(c);heal(c,100);release(c);c['manual_controls']=True;c['controls'][0]={'sequence':[dict(action='cover',t=.2,duration=.1)]}
    c=add('other-caster-store');store(c,target='all_allies');c['owners'][-1]=4;c['environment']['allies'][4]['base_hp']=20000;heal(c,100,target='all_allies');attack(c)
    c=add('pool-still-active');c['duration']=.3;pool(c);heal(c,100)
    c=add('mixed-actors-store');c.update(sampled_delivery=True,sampled_routed_delivery=True);store(c);pool(c);effect(c,field('lifesteal_pct',100,'self','life'));release(c)
    c['patterns'].append(dict(id='healing-adds',kind='summon',spec=dict(count=2,hp=10000)))
    from portable_coordinate_sampled_skill_cases import damage
    effect(c,dict(damage('mixed-skill'),target='all_enemies'))
    return rows
