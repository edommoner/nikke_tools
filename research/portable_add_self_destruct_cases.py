"""Original complete rosters at final-shot, death and graph boundaries."""
import copy


def fixtures():
    from portable_add_attack_battle_cases import fixtures as original
    from portable_coordinate_original_resource_cases import fixtures as resources
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    template=original()[0]['body'];rows=[]
    for scenario in ('single-zero','spaced','coincident','renewal','body-mixed','hp-before-shot','time-close','EH-death-resources'):
        body=copy.deepcopy(resources()[0]['body'] if scenario.startswith('EH-') else template)
        attack=dict(atk=1000.,coeff=100.,target='all',hits=1,interval=0.)
        wave=dict(id='self-wave',kind='summon',spec=dict(count=6 if scenario.startswith('EH-') else 2,hp=1. if scenario=='hp-before-shot' else 1e12,attack=attack,attack_at=0. if scenario=='single-zero' else .25,self_destruct=True))
        if scenario in ('spaced','coincident','body-mixed','time-close'):
            attack.update(hits=3,interval=0. if scenario=='coincident' else .25)
        if scenario in ('hp-before-shot','time-close'):wave['spec']['attack_at']=.5
        if scenario=='renewal':wave.update(after=['start','self-wave'],repeat=2,until=dict(targets_cleared=True))
        if scenario=='time-close':wave['until']=dict(time=.25)
        patterns=[wave]
        if scenario=='body-mixed':patterns.insert(0,dict(id='body-first',kind='attack',spec=dict(atk=1000.,coeff=100.,target='all',hits=3,interval=.25)))
        body['enemy'].update(has_parts=False,patterns=copy.deepcopy(patterns))
        labels=[b.label for b in bindings(validate(patterns,coord=True)) if int(b.kind)==5]
        rows.append(dict(name='add-self-destruct-battle/'+scenario,body=body,patterns=patterns,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),
            logical_geometry=[dict(label=n,shape=dict(x=0.,y=0.,r=10000.,z=float(i+1))) for i,n in enumerate(labels)],
            contract=dict(scenario=scenario,original_profile='E.H.' if scenario.startswith('EH-') else '니힐리스타')))
    return rows
