"""Original Yuni/Yan battles with explicit physical attachments, not new skills."""
import copy
import engine_worker
from portable_enemy_movement_cases import fixtures as original

def fixtures():
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    rows=[]
    for i,source in enumerate([*original(),original()[0]]):
        row=copy.deepcopy(source);dead=i==5
        if dead:row['patterns'][0]['spec']['hp']=1.
        row['patterns'].append(dict(id='typed-attached-world',kind='idle',until=dict(time=31)))
        row['body']['enemy']['patterns']=copy.deepcopy(row['patterns'])
        owner=next(b for b in bindings(validate(row['patterns'],coord=True)) if int(b.kind)==5)
        kind=2 if i==1 else 3
        row.update(name='moving-typed/'+('owner-death' if dead else source['contract']['scenario']),
            character=source['contract']['owner'],coordinate_weapon_targets=True,max_attacks=128,
            typed_aim_policy=dict(mode='typed-before-body-v1'),typed_actor_policy=dict(mode='logical-owned-current-fields-v1'),
            typed_bindings=[dict(node='typed-attached-world',kind=kind,identity=100,capacity=1e30,owner=[5,owner.identity,1],label='moving-typed'),
                dict(node='typed-attached-world',kind=kind,identity=101,capacity=1e30,owner=[0,0,1],label='fixed-typed')],
            typed_geometry=dict(point_source='caster_aim',shapes=[dict(x=-190.,y=0.,r=30.,z=3.),dict(x=10000.,y=10000.,r=20.,z=0.)]),
            typed_attachment=dict(mode='visible-with-moving-owner-v1',bindings=[dict(typed_label='moving-typed',actor_label=owner.label)]))
        rows.append(row)
    return rows

def prepare(row):
    from portable_coordinate_typed_weapon_cases import prepare as weapons
    c,p=weapons(row)
    c.update({key:copy.deepcopy(row[key]) for key in ('logical_geometry','enemy_movement','typed_attachment','contract')})
    c.update(observe_actor_status=True,observe_enemy_fields=True,observe_named_state=True,observe_actor_pools=True,observe_counter_field_memberships=True,
        coordinate_packet_history='ordered-sha256-v1',python_observers_only=True,sampled_groups=True)
    return c,p
