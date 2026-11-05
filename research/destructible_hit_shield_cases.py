"""Plain real-scheduler skill packets consume one hit credit, not HP damage."""
import copy
from destructible_shield_battle_cases import fixtures as prior

def fixtures():
    old=prior();rows=[]
    def add(name,source=old[0],capacity=2.):
        c=copy.deepcopy(source);c.update(name='destructible-hit-shield/'+name,shield_interception_v1=True,hit_shield_interception_v1=True)
        for b in c['typed_bindings']:b.update(kind=4,capacity=capacity)
        for effect in c['effects']:
            actor=effect.get('target_counter',{}).get('actor')
            if actor is not None:actor['kind']='hit_shield'
        rows.append(c);return c
    add('two-packets-two-credits')
    add('break-without-damage-overflow',capacity=1.)
    c=add('hp-after-hit-shield',capacity=1.);c['typed_bindings'].append(dict(node='idle',kind=3,identity=11,capacity=5000.,owner=[0,0,1]))
    c=add('hit-after-hp-shield');c['typed_bindings'].insert(0,dict(node='idle',kind=3,identity=11,capacity=500.,owner=[0,0,1]))
    c=add('hp-factor-cannot-multiply-hit-credit',capacity=5.);c['effects'][0]['fixed_value']=900.
    c=add('projectile-factor-cannot-multiply-hit-credit');c['effects'][0]['stat']='projectile_dmg_pct'
    c=add('large-damage-still-one-credit',capacity=5.);c['effects'][1]['fixed_value']=100000.
    add('named-coefficient-keeps-credit-one',next(c for c in old if c['name'].endswith('/named-coefficient-is-preserved')),capacity=3.)
    add('named-child-consumes-separate-credit',next(c for c in old if c['name'].endswith('/named-completion-child-reselects-shield')))
    add('death-counter-child-falls-back-to-body',next(c for c in old if c['name'].endswith('/death-counter-child-falls-back-to-body')),capacity=1.)
    add('respawn-generation-credits-are-isolated',next(c for c in old if c['name'].endswith('/next-generation-is-selected-after-respawn')),capacity=1.)
    add('other-owner-does-not-intercept',next(c for c in old if c['name'].endswith('/other-owner-does-not-intercept')))
    add('expiry-does-not-consume-next-credit',next(c for c in old if c['name'].endswith('/expired-world-falls-back-to-body')))
    c=add('hp-factor-still-applies-to-hp-shields',capacity=10000.);c['typed_bindings'][0]['kind']=3
    c=add('legacy-hp-policy-skips-hit-shield');c['hit_shield_interception_v1']=False
    c=add('zero-coefficient-publishes-no-credit');c['effects'][1]['fixed_value']=0.
    c=add('threshold-child-consumes-third-credit',next(c for c in old if c['name'].endswith('/death-counter-child-falls-back-to-body')),capacity=3.)
    c['effects'][0]['target_counter'].update(threshold=2,on_death=False)
    add('stale-owner-generation-does-not-intercept',next(c for c in old if c['name'].endswith('/stale-owner-generation-does-not-intercept')))
    return rows
