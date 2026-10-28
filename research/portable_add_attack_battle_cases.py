"""Original Nihilister rosters; attacking ADDs use real finite health pools."""
import copy
from portable_original_identity_inventory import selected_profile_bodies


def fixtures():
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    original=selected_profile_bodies(['니힐리스타'],0)[0][2];rows=[]
    for scenario in ('alive','dead','renewal','interleaved','random','slots-pierce'):
        body=copy.deepcopy(original);body.update(duration=6,seed=4951)
        attack=dict(atk=1000,coeff=100,target='random:2' if scenario=='random' else 'slot:2,4' if scenario=='slots-pierce' else 'all',hits=32,interval=.25,pierce=scenario=='slots-pierce')
        wave=dict(id='incoming-wave',kind='summon',spec=dict(count=2,hp=1. if scenario=='dead' else 1e12,attack=attack))
        if scenario=='renewal':wave.update(after=['start','incoming-wave'],until=dict(time=2.),repeat=2)
        patterns=[wave]
        if scenario=='interleaved':
            patterns.append(dict(id='middle-body',kind='attack',spec=dict(atk=1000,coeff=100,target='all',hits=32,interval=.25)))
            last=copy.deepcopy(wave);last['id']='last-wave';last['spec']['count']=1;patterns.append(last)
        body['enemy'].update(has_parts=False,patterns=copy.deepcopy(patterns))
        actors=bindings(validate(patterns,coord=True));labels=[b.label for b in actors if int(b.kind)==5]
        rows.append(dict(name='add-attack-battle/Nihilister/'+scenario,body=body,patterns=patterns,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),
            logical_geometry=[dict(label=n,shape=dict(x=0.,y=0.,r=10000.,z=float(i+1))) for i,n in enumerate(labels)],
            contract=dict(scenario=scenario,definitions=70)))
    return rows
