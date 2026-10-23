"""Concurrent numeric/focus caches, shared healing and immutable part receipts."""
import copy
from portable_late_attack_random_cases import fixtures as late_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    seed=late_fixtures()[0];rows=[]
    for label,camera,healing,parts in (
        ('focus-owner',0,False,False),('focus-foreign',4,False,False),
        ('focus-empty',None,False,False),('focus-heal',0,True,False),
        ('focus-parts',0,False,True),('focus-heal-parts',0,True,True)):
        c=copy.deepcopy(seed);c['name']='mixed-query-'+label;names=roster_names(c)
        c['camera']=[] if camera is None else [names[camera]];c['camera_mode']='single'
        c['focus_aim_layer2']=True;c['environment']['focus_aim_layer2']=True
        c['observe_lifesteal']=True;c['observe_heal_sources']=True
        c['effects'].append(field('atk_pct',10,'all_allies','focused-numeric',timing='passive',condition=['focusing']))
        c['owners'].append(0)
        if healing:
            c['effects'] += [instant('current_hp_reduce',50,'all_allies','initial-drain'),
                             field('heal_split',0,'all_allies','shared-link'),
                             instant('heal_hp_pct',10,'self','post-shot-heal','on_attack')]
            c['owners'] += [0,0,0]
        if parts:
            c['patterns']=[dict(id='parts',kind='parts',targets=[dict(name='near',hp=1e8,reach=1),dict(name='far',hp=1e8,reach=5)])]
            c['effects'].append(dict(name='parts-source',source='스킬2',type='damage',stat='bonus_damage:2',fixed_value=100,target='all_enemies',hits_parts=True,trigger=dict(timing=['battle_start'],condition=[])))
            c['owners'].append(0)
        rows.append(c)
    return rows
