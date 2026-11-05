"""Actual canonical hand arbitration supplies the declared typed skill's point."""
import copy
from typed_geometry_cases import fixtures as spatial

def fixtures():
    rows=[]
    for label,offset,kind in [('auto',None,2),('hand-before-skill',1.9,2),('hand-on-skill-frame',2.,2),('shield-hand-before-skill',1.9,3)]:
        base=next(r for r in spatial() if r['probe_kind']==kind)
        c=copy.deepcopy(base);c['name']='coordinate-typed-live-aim/'+label
        for b in c['typed_bindings']:b['capacity']=1e12
        c['typed_geometry'].pop('point');c['typed_geometry']['point_source']='caster_aim'
        if offset is None:
            c['typed_geometry']['shapes']=[dict(x=0.,y=0.,r=3.,z=2.),dict(x=100.,y=0.,r=3.,z=1.)]
            c['expected_handles']=[[kind,10,1]]*2
        else:
            c['patterns'].append(dict(id='aim-parts',kind='parts',targets=[dict(name='aim-left',hp=1e30,x=-20.,y=0.,r=2.),dict(name='aim-right',hp=1e30,x=20.,y=0.,r=2.)]))
            c['typed_geometry']['shapes']=[dict(x=-20.,y=0.,r=3.,z=2.),dict(x=20.,y=0.,r=3.,z=1.)]
            owner=c['body']['squad'][0]
            c['declared_aim_controls']={owner:[dict(at='aim-right',priority=90,anchor='combat_start',offset=offset,len=10.),dict(at='aim-left',priority=90)]}
            c['expected_handles']=[[kind,10 if offset==2. else 11,1],[kind,11,1]]
        rows.append(c)
    return rows
