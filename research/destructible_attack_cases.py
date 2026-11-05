"""Resolved projectile attacks with GPU-owned live-set selection."""
import copy
from destructible_counter_cases import fixtures as counter_cases
from destructible_world_cases import binding,tick

def fixtures():
    seed=counter_cases()[0];rows=[]
    def add(name,bindings=None,**kw):
        c=copy.deepcopy(seed);c.update(name='destructible-attack/'+name,bindings=bindings or [binding()],ops=[tick(0),tick(.1)],damage=1000.,credit=1.,outcome=2,who=2,family=1,attack_id=123)
        c['effects'][0]['target_counter']['threshold']=1;c.update(kw);rows.append(c);return c
    mixed=[binding(),binding(identity=11),binding(kind=3,identity=12),binding(kind=4,identity=13,capacity=2)]
    add('mixed-live-only-projectiles',mixed)
    add('zero-damage-keeps-live',mixed,damage=0.)
    add('miss-no-counter',mixed,damage=0.,credit=0.,outcome=0)
    add('blocked-with-credit',mixed,damage=0.,outcome=1)
    add('fractional-credit',mixed,damage=.25,credit=.5)
    add('only-shields-empty',[binding(kind=3),binding(kind=4,identity=11,capacity=2)])
    c=add('delayed-empty');c['nodes']=[dict(id='a',delay=1)]
    c=add('new-generation');c['nodes']=[dict(id='a',after=['start','a'],repeat=2,until=dict(time=.1))]
    c=add('high-slot128',[binding(identity=1000+i) for i in range(128)]);c['effects'][0]['target_counter']['actor']['identity']=1127
    return rows
