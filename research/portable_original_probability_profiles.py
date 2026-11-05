"""Literal repeated hits test original probability effects without changing them."""
import copy

def profiles():
    from portable_original_identity_inventory import profile_bodies
    from portable_original_incoming_profiles import attack
    body=next(b for name,stage,b in profile_bodies() if name=='엠마' and stage==0)
    rows={}
    for scene in ('control','self-chipped','self-wounded','ally-chipped'):
        patterns=[dict(id='world',kind='idle',until=dict(time=30))]
        if scene=='self-wounded':patterns.append(attack('initial-wound',.5,800000,target='slot:1',ignore=True))
        if scene!='control':
            incoming=attack('received',1.,25000,target='slot:3' if scene=='ally-chipped' else 'slot:1',ignore=True)
            incoming['spec'].update(hits=64,interval=.04);patterns.append(incoming)
        rows['original-catalogue/probability/Emma-'+scene+'/30s']=dict(character='엠마',favorite_stage=0,kind=3,duration=30,body=copy.deepcopy(body),patterns=patterns,
            scene_witness=dict(family='Original-probability',scenario=scene))
    return rows
