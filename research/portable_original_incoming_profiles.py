"""Literal enemy attacks against unchanged original role and decoy rosters."""
import copy

def attack(name,time,amount,*,target='slot:3',ignore=False,pierce=True):
    return dict(id=name,kind='attack',delay=time,spec=dict(atk=amount,coeff=100,target=target,ignore_taunt=ignore,pierce=pierce,hits=1,interval=.1))

def profiles():
    from portable_original_role_profiles import profiles as roles
    from portable_original_identity_inventory import profile_bodies
    source=roles()['original-catalogue/role/Red-Hood-123/30s'];rows={}
    for scenario in ('B2','auto'):
        row=copy.deepcopy(source)
        if scenario=='auto':row.pop('declared_burst_sequence');row.pop('variant')
        row['patterns']=[dict(id='world',kind='idle',until=dict(time=30)),*[attack('incoming-'+str(t),t,400000) for t in (1.,4.,14.)]]
        row['scene_witness']=dict(family='Red-Hood',scenario=scenario)
        rows['original-catalogue/incoming/Red-Hood-'+scenario+'/30s']=row
    body=next(body for name,stage,body in profile_bodies() if name=='신데렐라' and stage==0)
    for scenario,amount in [('chipped',400000),('broken',3500000)]:
        rows['original-catalogue/incoming/Cinderella-'+scenario+'/30s']=dict(character='신데렐라',favorite_stage=0,kind=3,duration=30,body=copy.deepcopy(body),
            patterns=[dict(id='world',kind='idle',until=dict(time=30)),attack('decoy-first',4.,amount,target='slot:1',ignore=True,pierce=False),attack('decoy-check',5.,100000,target='slot:1',ignore=True,pierce=False)],
            scene_witness=dict(family='Cinderella',scenario=scenario))
    return rows
