"""Authored literal geometry and events;no CPU decisions become GPU input."""
import copy
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'scripts')]
import engine_worker
from timer_registry_cases import NAMES
from portable_geometry_specs import from_roster
from calculator.buff_manager import optimal_range_of, _NIKKE


def effect(name, stat='atk_pct', value=1, conditions=None, timing='on_attack', duration=-1, **extra):
    return dict(name=name, source='스킬1', type='buff', stat=stat, fixed_value=value,
                duration=duration, target='self', max_stack=10,
                trigger=dict(timing=[timing], condition=conditions or []), **extra)


def geometry(**enemy):
    return from_roster([dict(name=n) for n in NAMES], enemy)


def case(name, conditions, enemy, *, owner=0, buffs=None, marker=None, script=None):
    effects=list(buffs or [])+[effect('marker', conditions=conditions)]
    return dict(name='geometry-'+name, geometry_reference=True, effects=effects,
        owners=[owner]*len(effects), environment=dict(geometry=geometry(**enemy)),
        script=script or [[0,0,0,owner,0,-1,0,0],[.1,0,7,owner,0,-1,0,0],[.1,2,0,0,0,0,0,0]],
        expected_queries=[], **(dict(expected_marker=marker) if marker is not None else {}))


def main():
    rows=[]
    for owner in range(5):
        for value in [0, .5, math.nextafter(1.,0), 1., math.nextafter(1.,math.inf),50]:
            rows.append(case(f'core-{owner}-{value}', ['core_hit'], dict(core_px=value), owner=owner, marker=int(value>=1)))
        name=NAMES[owner];weapon=_NIKKE[name]['weapon_type'];lo,hi=optimal_range_of(name,weapon)
        for minimum,maximum in [(0,0),(50,20),(100,100),(150,20)]:
            lower=max(0,lo*(1-minimum/100))-1e-9;upper=hi*(1+maximum/100)+1e-9
            buffs=[effect('minimum','optimal_range_min',minimum,timing='battle_start'),
                   effect('maximum','optimal_range_max_pct',maximum,timing='battle_start')]
            for index,(distance,expected) in enumerate([(math.nextafter(lower,-math.inf),False),(lower,True),
                    (math.nextafter(lower,math.inf),True),(math.nextafter(upper,-math.inf),True),
                    (upper,True),(math.nextafter(upper,math.inf),False)]):
                rows.append(case(f'range-{owner}-{minimum}-{maximum}-{index}', ['optimal_range'],dict(distance=distance),
                                 owner=owner,buffs=buffs,marker=int(expected)))
        for selected,expected in [([],False),([weapon],True),([w for w in ('AR','SMG','SG','SR','RL','MG') if w!=weapon],False)]:
            rows.append(case(f'list-{owner}-{expected}-{len(selected)}',['optimal_range'],dict(optimal_range_weapons=selected),owner=owner,marker=int(expected)))
    for predicate,enemy in [('core_hit',dict(core_px=0)),('optimal_range',dict(distance=1e6))]:
        for conditions in [[predicate,'prob:20'],['prob:20',predicate],['prob:100',predicate],['self_state:absent',predicate],
                           [predicate,'self_stat_above:atk_pct:0'],['self_stat_above:atk_pct:0',predicate]]:
            rows.append(case('ordered-'+'-'.join(conditions),conditions,enemy,marker=0))
    # The deferred exact-rounding chains share the same expected accumulator.
    for conditions in [['prob:100','prob:99.99999999999999','prob:0'],['prob:99.99999999999999','prob:100','prob:0']]:
        script=[]
        for i in range(20):script += [[i/10,0,7,0,0,-1,0,0],[i/10,2,0,0,0,i,0,0]]
        rows.append(case('endpoint-'+'-'.join(conditions),conditions,{},script=script))
    owner=next(i for i,n in enumerate(NAMES) if optimal_range_of(n,_NIKKE[n]['weapon_type'])[0]>0)
    lo,hi=optimal_range_of(NAMES[owner],_NIKKE[NAMES[owner]]['weapon_type'])
    for when,expected in [(.999999,1),(1.,0),(1.000001,0)]:
        rows.append(case(f'expiry-{when}',['optimal_range'],dict(distance=lo*.5),owner=owner,
            buffs=[effect('minimum','optimal_range_min',50,timing='battle_start',duration=1)],marker=expected,
            script=[[0,0,0,owner,0,-1,0,0],[when,0,7,owner,0,-1,0,0],[when,2,0,0,0,0,0,0]]))
    # Physical auto,charge-mode changes,and list-based changed-weapon membership.
    base_type=_NIKKE[NAMES[0]]['weapon_type'];base_lo,base_hi=optimal_range_of(NAMES[0],base_type)
    for distance,selected in [(base_hi+1,[]),((base_lo+base_hi)/2,[]),(None,[base_type]),(None,['SR'])]:
        for changed in (False,True):
            w=dict(enabled=True,base_weapon_type=base_type,mode='auto',coefficient=100,capacity=100,interval=.25,reload=1,
                   gauge=0,stage=3,cooldown=40)
            effects=[effect('range-min','optimal_range_min',50,timing='battle_start'),
                     effect('range-max','optimal_range_max_pct',20,timing='battle_start'),
                     effect('range-marker',value=1,conditions=['optimal_range'])]
            if changed:
                effects.insert(0,dict(name='changed',source='스킬1',type='weapon_change',target='self',weapon_type='SR',charge=False,
                    duration=2,damage_coeff={'10':100},max_ammo=100,fire_rate=4,reload_time=1,
                    trigger=dict(timing=['battle_start'],condition=[])))
            rows.append(dict(name=f'geometry-physical-{distance}-{selected}-{changed}',geometry_reference=True,
                geometry_physical_reference=True,effects=effects,owners=[0]*len(effects),expected_queries=[],
                environment=dict(geometry=geometry(distance=distance,optimal_range_weapons=selected)),
                combat=dict(weapons=[w]+[dict(enabled=False) for _ in range(4)],targets=[dict(hp=1e12)]),
                script=[[1,24,0,0,0,-1,0,0],[1,2,0,0,0,0,0,0]]))
    for row in rows:
        row['expected_queries']=[{} for command in row['script'] if command[1]==2]
        if 'expected_marker' in row:
            buffs=[0]*5;buffs[row['owners'][-1]]=row['expected_marker']
            row['expected_queries'][-1]={'attack_buffs':buffs}
    assert len({r['name'] for r in rows})==len(rows)
    (ROOT/'tests/fixtures/portable-geometry.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n')
    print('Authored geometry cases',len(rows))


if __name__ == '__main__':
    main()
