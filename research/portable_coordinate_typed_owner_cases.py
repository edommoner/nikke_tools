"""Original Prim current fields and a separately labelled real interception audit."""
import copy,importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('typed_owner_original_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));factory=importlib.util.module_from_spec(s);s.loader.exec_module(factory)
    rows=[]
    for label,duration in (('control',1.),('body',8.),('adds',8.),('manual-typed-with-adds',8.),('counter-owner-with-adds',8.)):
        body=dict(factory.body_for(factory.policy.roster_for('프림'),duration),burst_gauge_mode='accumulate',seed=4401)
        patterns=[dict(id='owned-shield',kind='idle',until=dict(time=duration+1))]
        body['enemy']['patterns']=copy.deepcopy(patterns)
        if label in ('adds','manual-typed-with-adds','counter-owner-with-adds'):patterns.append(dict(id='owner-adds',kind='summon',spec=dict(count=2,hp=1e30)))
        center=0. if label=='counter-owner-with-adds' else 10000.
        c=dict(name='coordinate-typed-owner/'+label,character='프림',body=body,patterns=patterns,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),coordinate_weapon_targets=True,max_attacks=128,
            typed_bindings=[dict(node='owned-shield',kind=3,identity=10+i,capacity=1e30,owner=[0,0,1],label='typed-'+n) for i,n in enumerate(('front','back'))],
            typed_geometry=dict(point_source='caster_aim',shapes=[dict(x=center,y=0.,r=100.,z=2.),dict(x=-10000.,y=0.,r=100.,z=1.)]),
            typed_aim_policy=dict(mode='typed-before-body-v1'),typed_actor_policy=dict(mode='body-owned-current-fields-v1'))
        if label=='manual-typed-with-adds':c['declared_aim_controls']={body['squad'][0]:[dict(at='typed-back',priority=90)]}
        if label=='counter-owner-with-adds':
            from target_counter_cases import marker
            e=marker(name='typed-owner-audit-marker',threshold=1,actor=dict(kind='hp_shield',identity=10,generation=1),families=['weapon'],attackers='squad',on_death=False)
            e['target']='boss';e['trigger']['timing']=['battle_start']
            field=dict(source='declared-owner-audit',name='typed-owner-audit-field',type='buff',stat='received_dmg_pct',fixed_value=17,target='target',duration=10,trigger=dict(timing=['event:target_counter_complete:typed-owner-audit-marker'],condition=['target_is_boss']))
            c['declared_owner_counter']=[e,field]
        rows.append(c)
    return rows

def prepare(row):
    from portable_coordinate_typed_weapon_cases import prepare as weapons
    c,p=weapons(row);c.update(observe_enemy_fields=True,observe_named_state=True,observe_actor_pools=True,observe_counter_field_memberships=True)
    c['declared_owner_counter']=copy.deepcopy(row.get('declared_owner_counter',[]))
    if c['declared_owner_counter']:
        from portable_typed_owner_declarations import declarations
        for effect,owner in declarations(c,c['original_run']['prepared']['effects']):
            c['effects'].append(copy.deepcopy(effect));c['owners'].append(0);p['effects'].append(dict(effect=copy.deepcopy(effect),owner=owner))
        c['observe_target_counters']=True
    return c,p
