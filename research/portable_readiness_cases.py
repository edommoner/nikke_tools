"""Priority-driven literal programs for both CUDA/Metal; full native oracle."""
import copy
from world_projectile_cases import fixtures as projectile_fixtures
from world_enemy_attack_cases import field


def fixtures():
    base = copy.deepcopy(projectile_fixtures()[0])
    base.update(duration=.45, state_queries=[], effects=[], owners=[])
    for ally in base['environment']['allies']:
        ally.update(base_hp=10000, base_defense=100)
    base['patterns'] = [dict(id='injury',kind='attack',delay=.05,
                            spec=dict(atk=300,coeff=100,target='all',hits=4,interval=.1,pierce=True))]
    rows = []
    for value, stack, duration in [(1,1,-1),(.125,3,-1),(-.5,1,-1),(1,1,.2)]:
        c = copy.deepcopy(base)
        c.update(name=f'lost-hp-defense-{value}-{stack}-{duration}',
                 effects=[field('def_pct',value,'self','lost-hp-defense',
                                scaling='lost_hp_pct',max_stack=stack,duration=duration)],owners=[0])
        if stack > 1:c['effects'][0]['trigger']['timing']=['on_attack']
        rows.append(c)
    for stat in ('def_pct','max_hp_only_pct'):
        c=copy.deepcopy(base)
        c.update(name='direct-health-runtime-'+stat,
                 effects=[field(stat,30,'self','direct-health',condition=['self_hp_above:99'])],owners=[0])
        rows.append(c)
    for ignore in (False,True):
        c=copy.deepcopy(base)
        c.update(name='typed-taunt-'+('ignore' if ignore else 'ranked'),
                 base_atk=[1000,2000,3000,4000,5000],
                 effects=[field('taunt',1,'enemies_top_atk:1','typed-taunt','on_attack')],owners=[0])
        c['patterns']=[dict(id='adds',kind='summon',spec=dict(count=2,hp=1e8,atk=1000000)),
                       dict(id='incoming',kind='attack',delay=.05,
                            spec=dict(atk=300,coeff=100,target='top_atk:1',ignore_taunt=ignore,hits=3,interval=.1,pierce=True))]
        rows.append(c)
    return rows
