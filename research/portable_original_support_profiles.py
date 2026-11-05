"""Literal incoming events and original Naga/Tia parties; no effect rewrites."""
import copy

def profiles():
    from portable_original_identity_inventory import profile_bodies
    from portable_original_incoming_profiles import attack
    from detail_coverage import body_for
    bodies={name:copy.deepcopy(body) for name,stage,body in profile_bodies() if stage==0 and name in ('나가','티아')}
    idle=dict(id='world',kind='idle',until=dict(time=30))
    early=[attack('hp-first',1.,400000,target='slot:1',ignore=True),
           attack('cover-first',1.1,400000,target='slot:1',ignore=True,pierce=False),
           attack('hp-second',1.2,350000,target='slot:3',ignore=True)]
    rows={}
    for character,label in [('나가','Naga'),('티아','Tia')]:
        rows['original-catalogue/support/'+label+'-injured/30s']=dict(character=character,favorite_stage=0,kind=3,duration=30,
            body=copy.deepcopy(bodies[character]),patterns=copy.deepcopy([idle,*early]),
            declared_manual_sequences={character:[dict(action='cover',t=.9,duration=.4)]},
            scene_witness=dict(family='Original-support',scenario=label+'-injured'))
    party=['나가','티아','드레이크','N102','메어리']
    body=dict(copy.deepcopy(body_for(party,30)),burst_gauge_mode='accumulate')
    for label in ('shield','injured-shield'):
        patterns=copy.deepcopy([idle] if label=='shield' else [idle,*early,attack('shield-hit',6.,100000,target='slot:1',ignore=True,pierce=False)])
        if label=='injured-shield':patterns[2]['spec']['target']='slot:2'
        rows['original-catalogue/support/Naga-Tia-'+label+'/30s']=dict(character='나가',favorite_stage=0,kind=3,duration=30,
            body=copy.deepcopy(body),patterns=copy.deepcopy(patterns),
            scene_witness=dict(family='Original-support',scenario='Naga-Tia-'+label))
        if label=='injured-shield':rows['original-catalogue/support/Naga-Tia-'+label+'/30s']['declared_manual_sequences']={'티아':[dict(action='cover',t=.9,duration=.4)]}
    return rows
