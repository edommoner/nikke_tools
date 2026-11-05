"""Declared spatial skills over live typed targets; originals and firing stay intact."""
import copy
from coordinate_typed_cases import fixtures as originals

def fixtures():
    base=copy.deepcopy(next(r for r in originals() if r.get('character')=='사쿠라'));rows=[]
    def case(label,shapes,*,capacity=1e12,duration=5,patterns=None,grow=0.,kind=2,character=None,expected=()):
        c=copy.deepcopy(base);c['name']='coordinate-typed-geometry/'+label;c['body']['duration']=duration
        if character:
            import importlib.util
            from pathlib import Path
            s=importlib.util.spec_from_file_location('typed_geometry_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
            c['body']=dict(f.body_for(f.policy.roster_for(character),duration),burst_gauge_mode='accumulate',seed=4201);c['character']=character
        c['patterns']=patterns or [dict(id='spatial',kind='idle',until=dict(time=duration))];c['body']['enemy']['patterns']=copy.deepcopy(c['patterns'])
        c['probe_kind']=kind;c['declared_effects'][0]['target']='typed_point';c['declared_effects'][0]['name']='declared-spatial-probe'
        c['typed_bindings']=[dict(node=c['patterns'][min(i,len(c['patterns'])-1)]['id'],kind=kind,identity=10+i,capacity=capacity,**(dict(owner=[0,0,1]) if kind==3 else {})) for i in range(len(shapes))]
        c['typed_geometry']=dict(point=[0.,0.],grow=grow,shapes=shapes);c['expected_handles']=[list(h) for h in expected];rows.append(c);return c
    circle=lambda z:dict(x=0.,y=0.,r=10.,z=z)
    case('destroy-front-reselect', [circle(2),circle(1)],capacity=1000,expected=[(2,10,1),(2,11,1)])
    case('rotated-rectangle-miss', [dict(x=100.,y=100.,w=4.,h=12.,rot=90.,z=2),circle(1)],expected=[(2,11,1),(2,11,1)])
    case('grow-rotated-rectangle', [dict(x=2.,y=0.,w=8.,h=2.,rot=90.,z=2),circle(1)],grow=1.,expected=[(2,10,1),(2,10,1)])
    case('birth-order-tie', [circle(1),circle(1)],patterns=[dict(id='older',kind='idle',until=dict(time=5)),dict(id='newer',kind='idle',delay=.5,until=dict(time=4.5))],expected=[(2,11,1),(2,11,1)])
    case('expiry-reselect', [circle(2),circle(1)],patterns=[dict(id='front',kind='idle',until=dict(time=3)),dict(id='back',kind='idle',until=dict(time=5))],expected=[(2,10,1),(2,11,1)])
    case('generation-reopen', [circle(1)],patterns=[dict(id='cycle',kind='idle',after=['start','cycle'],until=dict(time=3),repeat=2)],expected=[(2,10,1),(2,10,2)])
    case('hp-shield-front', [circle(2),circle(1)],kind=3,character='레이',capacity=1000,expected=[(3,10,1),(3,11,1)])
    case('point-misses-all', [dict(x=100.,y=100.,r=1.,z=3)],duration=3,expected=[])
    return rows
