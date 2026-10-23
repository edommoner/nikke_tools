"""Received-healing pool contracts, distinct from excess-healing damage storage."""
import copy
from portable_parent_fixed_cases import fixtures as parent
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant as raw_instant

def instant(stat,value,target,name,timing="battle_start",**kw):
    effect=raw_instant(stat,value,target,name,timing);effect.update(kw);return effect
from world_frame_native import roster_names

def fixtures():
    seed=copy.deepcopy(parent()[0]);seed.update(effects=[],owners=[],duration=.95);rows=[]
    def pool(value=150,**kw):return field('heal_overcharge_store_atk_pct',value,'self','pool',duration=.4,**kw)
    def heal(value=10,target='self',timing='battle_start',**kw):return instant('heal_hp_pct',value,target,'deposit',timing,**kw)
    def release(target='all_allies',timing='event:state_end:pool',**kw):return instant('heal_overcharge_discharge',0,target,'release',timing,target_effect='pool',**kw)
    def add(kind,effects,owners=None):
        c=copy.deepcopy(seed);c.update(name='heal-charge-'+kind,effects=[field('crit_rate',-100,'all_allies','no-crit')]+effects,owners=[0]+(owners or [0]*len(effects)),contract=dict(kind=kind));rows.append(c);return c
    add('empty',[pool(),release()])
    add('full-HP',[pool(),heal(),release()])
    add('damaged',[instant('current_hp_reduce',50,'all_allies','drain'),pool(),heal(),release()])
    add('capacity-clamp',[pool(),heal(100),release()])
    add('zero-capacity',[pool(0),heal(),release()])
    add('negative-capacity',[pool(-30),heal(),release()])
    add('negative-heal',[pool(),heal(-10),release()])
    add('live-bonus',[pool(),field('accumulate_max_scale_pct',100,'self','bonus',target_effect='pool'),heal(100),release()])
    add('wrong-bonus-name',[pool(),field('accumulate_max_scale_pct',100,'self','bonus',target_effect='other'),heal(100),release()])
    add('unrestricted-bonus',[pool(),field('accumulate_max_scale_pct',100,'self','bonus'),heal(100),release()])
    add('expired-bonus-keeps-amount',[pool(),field('accumulate_max_scale_pct',100,'self','bonus',duration=.2,target_effect='pool'),heal(100),release()])
    add('source-ATK-snapshot',[pool(),field('atk_pct',100,'self','later-atk','every:0.1s',max_trigger=1),heal(100,timing='every:0.2s',max_trigger=1),release()])
    add('initial-ATK',[field('atk_pct',100,'self','initial-atk'),pool(),heal(100),release()])
    add('one-discharge',[pool(),heal(100),release(timing='every:0.2s',max_trigger=2)])
    add('missing-name',[pool(),heal(),instant('heal_overcharge_discharge',0,'all_allies','other','every:0.2s',target_effect='absent',max_trigger=1)])
    add('refresh-resets-quantity',[pool(timing='every:0.2s',max_trigger=2),heal(100,timing='every:0.3s',max_trigger=1),release()])
    add('named-removal-retains',[pool(),heal(),instant('remove_named_buff',0,'self','remove','every:0.2s',target_effect='pool',max_trigger=1),release()])
    c=add('cleanse-discards',[pool(),heal(),instant('debuff_cleanse',0,'self','cleanse','every:0.2s',max_trigger=1),release(timing='every:0.3s',max_trigger=1)]);c['effects'][1]['polarity']='harmful'
    names=roster_names(seed)
    add('ordered-duplicate-recipients',[instant('current_hp_reduce',50,'all_allies','drain'),pool(),heal(),release([names[1],names[2],names[1]])])
    add('live-other-pool-receives-release',[pool(),field('heal_overcharge_store_atk_pct',300,'all_allies','second',duration=.8),heal(),release()])
    add('source-outgoing-and-received',[field('outgoing_heal_pct',50,'self','outgoing'),field('heal_received_pct',50,'all_allies','received'),pool(1000),heal(),release()])
    add('lifesteal',[pool(),field('lifesteal_pct',100,'self','life'),release()])
    c=add('down-discards',[pool(),heal(),release(timing='every:0.5s',max_trigger=1)]);c['patterns']=[dict(id='down',kind='attack',delay=.2,spec=dict(atk=1e12,coeff=100,target='slot:1',ignore_taunt=True))]
    add('repair-does-not-deposit',[pool(),instant('cover_heal_pct',100,'self','repair'),release()])
    add('shared-scalar-pool',[field('heal_overcharge_store_atk_pct',150,'all_allies','pool',duration=.4),heal(target='all_allies'),release()])
    c=add('other-owner',[pool(),heal(target=names[4],timing='every:0.1s',max_trigger=1),release()],[4,0,4]);c['base_atk'][4]=2000
    c=add('owner-order-before-activation',[pool(),heal(target=names[4]),release()],[4,0,4]);c['base_atk'][4]=2000
    add('other-caster-bonus',[pool(),field('accumulate_max_scale_pct',50,names[0],'other-source',target_effect='pool'),heal(100,timing='every:0.1s',max_trigger=1),release()],[0,3,0,0])
    add('other-caster-bonus-late-in-order',[pool(),field('accumulate_max_scale_pct',50,names[0],'other-source',target_effect='pool'),heal(100),release()],[0,3,0,0])
    return rows
