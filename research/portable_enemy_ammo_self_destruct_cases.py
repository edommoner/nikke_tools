"""Original Velvet roster with declared final-queue magazine boundaries."""
import copy


def fixtures():
    from portable_enemy_ammo_cases import fixtures as ammo_cases
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    original=ammo_cases()[0];rows=[]
    for scenario in ('single-zero','spaced','coincident','empty','reload-final','renewal','hp-before-shot','time-close'):
        body=copy.deepcopy(original['body'])
        attack=dict(atk=1000.,coeff=100.,target='all',hits=1,interval=0.)
        wave=dict(id='self-ammo',kind='summon',spec=dict(count=2,hp=1. if scenario=='hp-before-shot' else 1e12,
            attack=attack,attack_at=0. if scenario=='single-zero' else .25,self_destruct=True))
        if scenario in ('spaced','coincident','reload-final'):
            attack.update(hits=3,interval=0. if scenario=='coincident' else .25)
        if scenario in ('hp-before-shot','time-close'):wave['spec']['attack_at']=.5
        if scenario=='time-close':wave['until']=dict(time=.25)
        if scenario=='renewal':wave.update(after=['start','self-ammo'],repeat=2,until=dict(targets_cleared=True))
        patterns=[wave];body['enemy']['patterns']=copy.deepcopy(patterns)
        labels=[b.label for b in bindings(validate(patterns,coord=True)) if int(b.kind)==5]
        initial=0 if scenario=='empty' else 1 if scenario=='reload-final' else 16
        rows.append(dict(name='enemy-ammo-self-destruct/'+scenario,body=body,patterns=patterns,
            coord=copy.deepcopy(original['coord']),
            logical_geometry=[dict(label=n,shape=dict(x=0.,y=0.,r=10000.,z=float(i+1))) for i,n in enumerate(labels)],
            enemy_ammo=[dict(label=n,capacity=16,initial=initial,reload_seconds=1.,cancel_on_full=True) for n in labels],
            contract=dict(scenario=scenario,definitions=76)))
    return rows
