"""Full original Velvet rosters with explicitly declared scheduled magazines."""
import copy
from portable_original_identity_inventory import selected_profile_bodies

def fixtures():
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    original=selected_profile_bodies(['벨벳'],0)[0][2];rows=[]
    for scenario in ('level10','level1','late-empty','renewal','dead','body'):
        body=copy.deepcopy(original);body.update(duration=6,seed=4801)
        level=1 if scenario=='level1' else 10
        body['profile']['chars']['벨벳']['skill_levels']['1']=level
        attack=dict(atk=1000,coeff=100,target='all',hits=32,interval=.25)
        wave=dict(id='ammo-wave',kind='summon',spec=dict(count=2,hp=1. if scenario=='dead' else 1e12,attack=attack))
        if scenario=='late-empty':wave['delay']=2.
        if scenario=='renewal':wave.update(after=['start','ammo-wave'],until=dict(time=2.),repeat=2)
        if scenario=='body':wave['spec'].pop('attack')
        patterns=[wave]
        if scenario=='body':patterns.append(dict(id='body-attempts',kind='attack',spec=copy.deepcopy(attack)))
        body['enemy'].update(has_parts=False,patterns=copy.deepcopy(patterns))
        actors=bindings(validate(patterns,coord=True));labels=[b.label for b in actors if int(b.kind)==5]
        magazine_labels=(['__enemy__'] if scenario in ('level10','level1','body') else [])+labels
        initial=3 if scenario in ('renewal','dead') else 16
        rows.append(dict(name='enemy-ammo/Velvet/'+scenario,body=body,patterns=patterns,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),
            logical_geometry=[dict(label=n,shape=dict(x=0.,y=0.,r=10000.,z=float(i+1))) for i,n in enumerate(labels)],
            enemy_ammo=[dict(label=n,capacity=16,initial=initial,reload_seconds=1.,cancel_on_full=True) for n in magazine_labels],
            contract=dict(scenario=scenario,skill_level=level,definitions=76)))
    return rows
