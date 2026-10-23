"""Literal damage-accumulation worlds; no simulation, compiler or packing."""
import copy
from portable_parent_fixed_cases import fixtures as parent
from world_enemy_attack_cases import field
from portable_heal_charge_cases import instant
from world_frame_native import roster_names

def fixtures():
    seed=copy.deepcopy(parent()[0]);seed.update(duration=.95,effects=[],owners=[]);names=roster_names(seed);rows=[]
    def pool(stat='dmg_accum_dealt_atk_pct',value=1000,name='pool',target='target',timing='battle_start',duration=.4,**kw):return field(stat,value,target,name,timing,duration,**kw)
    def rate(value=50,name='rate',target='self',timing='battle_start',**kw):return field('dmg_accum_rate_pct',value,target,name,timing,**kw)
    def release(name='release',ref='pool',timing='event:state_end:pool',**kw):return dict(name=name,source='스킬2',type='damage',stat='accum_split_damage',target='all_enemies',target_effect=ref,trigger=dict(timing=[timing],condition=[]),**kw)
    def add(kind,effects,owners=None):
        c=copy.deepcopy(seed);c.update(name='damage-accum-'+kind,effects=[field('crit_rate',-100,'all_allies','no-crit')]+effects,owners=[0]+(owners or [0]*len(effects)),contract=dict(kind=kind));rows.append(c);return c
    add('dealt-default',[pool(),release()])
    add('received-default',[pool('dmg_accum_received_atk_pct'),release()])
    add('last-owner-dealt',[pool(),release()],[4,4])
    c=add('dealt-ignores-other-casters',[pool(),release()]);c['combat']['weapons'][0].update(charge=10,interval=11)
    c=add('received-counts-other-casters',[pool('dmg_accum_received_atk_pct'),release()]);c['combat']['weapons'][0].update(charge=10,interval=11)
    add('base50',[pool(),rate(),release()])
    add('base50-named25',[pool(),rate(),rate(25,'named',target_effect='pool'),release()])
    absent=rate();absent.pop('fixed_value')
    add('absent-base',[pool(),absent,release()])
    add('explicit-zero-base',[pool(),rate(0),release()])
    add('absent-base-named25',[pool(),absent,rate(25,'named',target_effect='pool'),release()])
    add('zero-base-named25',[pool(),rate(0),rate(25,'named',target_effect='pool'),release()])
    empty=copy.deepcopy(absent);empty['values']={};add('empty-values-is-zero',[pool(),empty,release()])
    add('wrong-named-rate',[pool(),rate(25,target_effect='other'),release()])
    add('wrong-caster-rate',[pool(),rate(25,target=names[0]),release()],[0,1,0])
    add('own-rate-wrong-recipient',[pool(),rate(50,target=names[4]),release()])
    add('two-baseline-rates',[pool(),rate(25),rate(50,'other-rate'),release()])
    add('negative-rate',[pool(),rate(-50),release()])
    add('cap-clamp',[pool(value=50),release()])
    add('zero-cap',[pool(value=0),release()])
    add('negative-cap',[pool(value=-100),release()])
    add('epsilon-inside',[pool(value=90.00000000005),release()])
    add('epsilon-outside',[pool(value=90.0000000002),release()])
    add('initial-ATK',[field('atk_pct',100,'self','initial-atk'),pool(value=100),release()])
    add('later-ATK-keeps-cap',[pool(value=100),field('atk_pct',100,'self','later-atk','every:0.1s',max_trigger=1),release()])
    add('empty-expiry',[pool(duration=.05),release()])
    add('archived-consume-once',[pool(),release(),release('again',timing='every:0.6s',max_trigger=1)])
    add('active-consume-once',[pool(duration=1.5),release(timing='every:0.4s',max_trigger=2)])
    add('missing-name',[pool(),release(ref='absent',timing='every:0.5s',max_trigger=1)])
    add('cross-owner-active',[pool(duration=1.5),release(timing='every:0.4s',max_trigger=1)],[0,1])
    add('cross-owner-archive',[pool(),release(timing='every:0.5s',max_trigger=1)],[0,1])
    c=add('refresh-clears-archive',[pool(timing='every:0.2s',duration=.3,max_trigger=2),release()])
    kept=copy.deepcopy(c);kept.update(name='damage-accum-refresh-collects-new-lifetime',contract=dict(kind='refresh-collects-new-lifetime'));rows.append(kept)
    c['combat']['weapons'][0].update(capacity=1,reload=10)
    add('named-removal-retains-archive',[pool(duration=.8),instant('remove_named_buff',0,'self','remove','every:0.4s',target_effect='pool',max_trigger=1),release(timing='every:0.5s',max_trigger=1)])
    add('split-only-and-int-truncation',[pool(),field('split_dmg_pct',25.19,'self','split-only','event:state_end:pool'),release()])
    add('no-second-attack-modifier',[pool(),field('atk_dmg_pct',100,'self','late-modifier','event:state_end:pool'),release()])
    add('lifesteal-before-rate',[instant('current_hp_reduce',50,'all_allies','drain'),pool(),field('lifesteal_pct',100,'self','life'),rate(1,scaling='lost_hp_pct'),release()])
    c=add('scatter-two-muzzles',[pool(),release()]);c['combat']['weapons'][0].update(pellets=3,muzzles=2)
    c=add('add-share-excluded',[pool(),release()]);c['patterns'].append(dict(id='adds',kind='summon',spec=dict(count=2,hp=1e8)))
    c=add('explicit-boss-share',[pool(),dict(name='split-source',source='스킬2',type='damage',stat='split_damage',fixed_value=100,target='all_enemies',trigger=dict(timing=['every:0.1s'],condition=[]),max_trigger=1),release()]);c['patterns'].append(dict(id='adds',kind='summon',spec=dict(count=2,hp=1e8)))
    add('all-pools-full-before-notices',[pool(value=50,name='first',duration=1.5),pool('dmg_accum_received_atk_pct',value=50,name='second',duration=1.5),release('first-release',ref='first',timing='event:accum_full:first'),release('second-release',ref='second',timing='event:accum_full:second')],[0,1,0,1])
    add('duplicate-name-first-active',[pool(duration=1.5),pool('dmg_accum_received_atk_pct',duration=1.5),release(timing='every:0.4s',max_trigger=1),release('again',timing='every:0.45s',max_trigger=1)],[0,1,2,3])
    add('duplicate-name-last-archive',[pool(),pool('dmg_accum_received_atk_pct'),release(timing='every:0.5s',max_trigger=1)],[0,1,2])
    add('pool-target-does-not-filter-damage',[pool(target=names[4],duration=1.5),release(timing='every:0.4s',max_trigger=1)])
    add('stacked-rate',[pool(),rate(100,timing='every:0.1s',max_trigger=2,max_stack=2),release()])
    c=add('down-keeps-name-archive',[pool(target='self'),release(timing='every:0.5s',max_trigger=1)],[0,1]);c['patterns']=[dict(id='down',kind='attack',delay=.36,spec=dict(atk=1e12,coeff=100,target='slot:1',ignore_taunt=True,pierce=True))]
    add('release-feeds-another-pool',[pool(),pool('dmg_accum_received_atk_pct',name='second',duration=.7),release(),release('second-release',ref='second',timing='event:state_end:second')],[0,1,0,1])
    add('rate-expired-before-hit',[pool(),rate(50,duration=.1),release()])
    c=add('last-owner-cap-snapshot',[pool('dmg_accum_received_atk_pct',value=100),release()],[4,4]);c['base_atk'][4]=2000
    add('dealt-group-before-received',[pool('dmg_accum_received_atk_pct',value=50,name='received-first',duration=1.5),pool(value=50,name='dealt-second',duration=1.5),release('dealt-release',ref='dealt-second',timing='event:accum_full:dealt-second'),release('received-release',ref='received-first',timing='event:accum_full:received-first')])
    add('ordered-baseline-cancellation',[pool(),rate(1e16,'large'),rate(-1e16,'cancel'),rate(1,'unit'),release()])
    add('separate-baseline-and-named-groups',[pool(),rate(1e16,'large'),rate(1,'named',target_effect='pool'),rate(-1e16,'cancel'),release()])
    add('duplicate-name-active-reverse-stat-order',[pool('dmg_accum_received_atk_pct',duration=1.5),pool(duration=1.5),release(timing='every:0.4s',max_trigger=1),release('again',timing='every:0.45s',max_trigger=1)],[0,1,2,3])
    return rows
