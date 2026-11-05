"""Original ammo-world graphs and explicit component lifecycle stimuli."""
import copy


def fixtures():
    from portable_enemy_ammo_cases import fixtures as ammo
    rows=[]
    for r in ammo():
        # Death here is an authored component stimulus, not the original roster's
        # HP death. The complete battle remains a separate integration contract.
        if r['contract']['scenario'] in ('level1','dead'):continue
        rows.append(dict(name='add-attack/'+r['contract']['scenario'],patterns=copy.deepcopy(r['patterns']),clock='accumulated',duration=6))
    attack=lambda hits,interval:dict(atk=100,coeff=100,target='all',hits=hits,interval=interval)
    summon=dict(id='first-add',kind='summon',spec=dict(count=2,hp=100,attack=attack(4,.2)),until=dict(targets_cleared=True),repeat=2,after=['start','first-add'])
    body=dict(id='middle-body',kind='attack',spec=attack(3,.3))
    last=dict(id='last-add',kind='summon',spec=dict(count=1,hp=100,attack=attack(3,0)))
    rows.append(dict(name='add-attack/interleaved-clear-renewal',patterns=[summon,body,last],frames=[[0,0],[.2,0],[.4,1],[.6,0],[1.,0]],duration=1))
    rows.append(dict(name='add-attack/sparse-catchup',patterns=[dict(id='sparse',kind='summon',spec=dict(count=3,hp=100,attack=attack(7,.1)))],frames=[[0,0],[.55,0],[.7,0]],duration=.7))
    rows.append(dict(name='add-attack/rational-clock',patterns=[dict(id='rational',kind='summon',delay=.1,spec=dict(count=1,hp=100,attack=attack(5,.1)))],clock='rational',duration=.6))
    rows.append(dict(name='add-attack/expired-before-due',patterns=[dict(id='expires',kind='summon',until=dict(time=.2),spec=dict(count=1,hp=100,attack=attack(5,.1)))],frames=[[0,0],[.1,0],[.2,0],[.6,0]],duration=.6))
    return rows
