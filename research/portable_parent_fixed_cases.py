"""Parent-notification quantities, not recomputed coefficient damage."""
import copy
from portable_nonfull_charge_cases import fixtures as partial
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    seed=copy.deepcopy(next(c for c in partial() if c['name']=='nonfull-charge-automatic-full-only'))
    seed.update(effects=[],owners=[],state_queries=[],duration=.95,base_atk=[1000]*5,post_fire_delays=[.215]*5,contract={})
    seed['enemy']['def']=100;seed['enemy']['has_parts']=False
    for w in seed['combat']['weapons']:w.update(coefficient=100,full_charge_mult=100,pellets=1,muzzles=1)
    rows=[]
    def add(label,*,pct=33.3,owner=0,target='target_body',timing='full_charge_hit'):
        c=copy.deepcopy(seed);c['name']='parent-fixed-'+label
        c['effects']=[field('crit_rate',-100,'all_allies','no-crit'),dict(name='fixed-parent',source='스킬2',type='damage',stat='dealt_fixed_damage',fixed_value=pct,target=target,trigger=dict(timing=[timing],condition=[]))];c['owners']=[0,owner]
        c['contract']=dict(kind=label,pct=pct,owner=owner);rows.append(c);return c
    add('basic');add('one-hundred',pct=100);add('zero',pct=0);add('negative',pct=-30);add('fraction-to-zero',pct=.01)
    c=add('scatter-two-muzzles');c['combat']['weapons'][0].update(pellets=3,muzzles=2)
    c=add('seven-pellets');c['combat']['weapons'][0]['pellets']=7
    add('last-owner',owner=4);add('boss',target='boss');add('inherited-target',target='target')
    c=add('all-enemies',target='all_enemies');c['patterns'].append(dict(id='adds',kind='summon',spec=dict(count=2,hp=1e8)))
    add('context-absent-at-battle-start',timing='battle_start')
    add('context-absent-at-hit-count',timing='hit_count')
    c=add('context-absent-spends-budget');c['effects'][-1].update(max_trigger=1);c['effects'][-1]['trigger']['timing']=['hit_count','full_charge_hit']
    c=add('budget-one');c['effects'][-1]['max_trigger']=1
    c=add('every-second',timing='full_charge_hit_count:2')
    c=add('duplicate');c['effects'][-1]['trigger']['timing']*=2
    c=add('false-condition');c['effects'][-1]['trigger']['condition']=['during_full_burst']
    c=add('no-second-modifiers');c['effects'].extend([field('atk_dmg_pct',100,'self','later-damage','full_charge_hit'),field('dmg_scale_mag_pct',100,'self','fixed-magnitude','battle_start',target_effect='fixed-parent')]);c['owners'].extend([0,0])
    c=add('nested-context-empty');c['effects'].insert(1,instant('current_hp_reduce',50,'all_allies','drain')) ;c['owners'].insert(1,0)
    c['effects'].insert(2,instant('heal_hp_pct',10,'self','heal-first','full_charge_hit'));c['owners'].insert(2,0)
    child=copy.deepcopy(c['effects'][3]);child.update(name='nested-fixed');child['trigger']['timing']=['event:heal_received'];c['effects'].append(child);c['owners'].append(0)
    c=add('lifesteal');c['effects'].insert(1,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(1,0);c['effects'].insert(2,field('lifesteal_pct',100,'self','life'));c['owners'].insert(2,0)
    c=add('nonfull-only');c['controls'][0]=dict(click=[dict(window='always',mode='tap',rate=4,release=.05)])
    c=add('large-quantity');c['base_atk'][0]=10**15;c['combat']['weapons'][0]['pellets']=7
    return rows
