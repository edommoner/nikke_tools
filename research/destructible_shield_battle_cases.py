"""Declared boss-skill interception on the real battle clock, not input hits."""
import copy
from destructible_modifier_battle_cases import fixtures as previous

def fixtures():
    seeds=previous();plain=seeds[0];rows=[]
    def add(name,source=plain):
        c=copy.deepcopy(source);c['name']='destructible-shield-battle/'+name
        for effect in c['effects']:
            if effect.get('target')=='all_projectiles':effect['target']='boss'
            if effect.get('stat')=='projectile_dmg_pct':effect['stat']='shield_dmg_pct'
        for b in c['typed_bindings']:b.update(kind=3,owner=[0,0,1])
        rows.append(c);return c
    add('shield-factor-keeps-physical-body')
    c=add('projectile-factor-does-not-affect-shield');c['effects'][0]['stat']='projectile_dmg_pct'
    c=add('break-without-overflow');c['typed_bindings'][0]['capacity']=500.
    c=add('unowned-shield-does-not-intercept');c['typed_bindings'][0].pop('owner')
    c=add('other-owner-does-not-intercept');c['typed_bindings'][0]['owner']=[5,0,1]
    c=add('stale-owner-generation-does-not-intercept');c['typed_bindings'][0]['owner']=[0,0,2]
    c=add('two-shields-in-binding-order');c['typed_bindings'][0]['capacity']=500.;c['typed_bindings'].append(dict(node='idle',kind=3,identity=11,capacity=5000.,owner=[0,0,1]))
    c=add('expired-world-falls-back-to-body');c['patterns'][0]['until']['time']=.15
    add('named-coefficient-is-preserved',next(c for c in seeds if c['name'].endswith('/named-coefficient-is-preserved')))
    add('expiry-before-second-skill',next(c for c in seeds if c['name'].endswith('/expiry-before-second-skill')))
    add('ordinary-and-target-factor-add',next(c for c in seeds if c['name'].endswith('/ordinary-and-target-factor-add')))
    c=add('projectiles-are-not-shields');c['typed_bindings'][0]['kind']=2
    add('named-completion-child-reselects-shield',next(c for c in seeds if c['name'].endswith('/named-completion-keeps-body-normal')))
    c=add('death-counter-child-falls-back-to-body');c['typed_bindings'][0]['capacity']=500.
    from target_counter_cases import marker
    m=marker(threshold=99,actor=dict(kind='hp_shield',identity=10,generation=1),on_death=True,attackers='squad');m['target']='boss';m['trigger']['timing']=['battle_start']
    child=copy.deepcopy(c['effects'][1]);child.update(name='shield-death-child',fixed_value=50.,max_trigger=1,trigger=dict(timing=['event:target_counter_complete:marker'],condition=[]))
    c['effects']=[m,*c['effects'],child];c['owners']=[0,*c['owners'],0];c['observe_target_counters']=True
    c=add('next-generation-is-selected-after-respawn');c['typed_bindings'][0]['capacity']=500.
    c['patterns'][0].update(after=['start','idle'],repeat=3,until=dict(time=.1),emit=['event:target_spawn'])
    c['effects'][1].update(trigger=dict(timing=['event:target_spawn'],condition=[]),max_trigger=3)
    return rows
