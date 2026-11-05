"""Declared typed-before-body candidates; originals are never stripped to fit."""
import copy
from portable_coordinate_typed_weapon_cases import fixtures as weapons

def fixtures():
    rows=[];base=weapons()[0]
    for label in ('fallback','destroy-next-frame','manual-canonical','manual-typed','adds-first','full-burst-follow','gap-current-skill'):
        c=copy.deepcopy(weapons()[3] if label=='gap-current-skill' else base);c['name']='coordinate-typed-aim/'+label
        duration=30 if label=='full-burst-follow' else 1 if label=='destroy-next-frame' else 3
        c['body']['duration']=duration;c['patterns']=[dict(id='typed-weapon-world',kind='idle',until=dict(time=duration))]
        c['body']['enemy']['patterns']=copy.deepcopy(c['patterns']);kind=3 if label=='gap-current-skill' else 2
        c['typed_bindings']=[dict(node='typed-weapon-world',kind=kind,identity=10+i,capacity=1. if label=='destroy-next-frame' else 1e30,label='typed-'+name,**(dict(owner=[0,0,1]) if kind==3 else {})) for i,name in enumerate(('front','back'))]
        c['typed_geometry']=dict(point_source='caster_aim',shapes=[dict(x=10000.,y=0.,r=100.,z=2.),dict(x=-10000.,y=0.,r=100.,z=1.)])
        c['typed_aim_policy']=dict(mode='typed-before-body-v1');c['typed_aim_witness']=label
        if label=='manual-canonical':
            c['patterns'].append(dict(id='manual-part',kind='parts',targets=[dict(name='manual-part',hp=1e30,x=30000.,y=0.,r=100.,z=3.)]))
        if label in ('manual-canonical','manual-typed','full-burst-follow'):
            at='manual-part' if label=='manual-canonical' else 'typed-back'
            c['declared_aim_controls']={c['body']['squad'][0]:[dict(at=at,priority=90)]}
        if label=='adds-first':c['patterns'].append(dict(id='adds',kind='summon',spec=dict(count=1,hp=1e30)))
        if label=='gap-current-skill':c['expect_reference_gap']='enemies_nearest_in_range'
        rows.append(c)
    return rows
