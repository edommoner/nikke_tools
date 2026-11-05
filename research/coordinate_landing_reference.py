"""Expected landing on the selected deterministic geometry/power/GL profile."""
import math
import portable_coordinate_numeric_v1 as n
import portable_coordinate_power_v1 as p
from portable_coordinate_quadrature_v1 import nodes
from coordinate_geometry_reference import evaluate as shape,finite

def landing(case):
    import engine_worker
    from calculator import aim
    from portable_coordinate_landing_v1 import TARGETS,CONSTANTS
    targets=case['targets'];core=case.get('core');ax,ay=case['aim'];R=max(case['radius'],1e-9);grow=case['grow'];k=case['k']
    finite(ax,ay,case['radius'],grow,k)
    if len(targets)>TARGETS or grow<0 or not n.number(CONSTANTS['MIN_K'])<=k<=n.number(CONSTANTS['MAX_K']):raise ValueError('Landing domain')
    def geometry(s,rho=0.,grow=0.):return shape((*s,ax,ay,rho,grow))
    def power(x,y):return n.number(p.evaluate(n.bits(x),n.bits(y)))
    near=[i for i,s in enumerate(targets) if geometry(s)['distance']<=R+grow]
    use_core=core is not None and geometry(core)['distance']<=R
    front=[0.]*len(targets);reach=[0.]*len(targets)
    result=dict(reference_kind='deterministic-common-cpu',contract='coordinate-landing-v1',front=front,reach=reach,core_open=0.,core_under=0.,cuts=[],nodes=0,near_count=len(near),use_core=use_core,fast_path=0)
    if not near and not use_core:result['fast_path']=1;return result
    if not near and core[0]==1 and core[1]==ax and core[2]==ay:
        probability=power(min(1.,core[3]/R),k);result.update(core_open=probability,core_under=probability,fast_path=2);return result
    cuts={0.,1.}
    for i in near:
        for value in geometry(targets[i])['breaks']:
            if 0.<value<R:cuts.add(power(value/R,k))
        if grow>0:
            for value in geometry(targets[i],grow=grow)['breaks']:
                if 0.<value<R:cuts.add(power(value/R,k))
    if use_core:
        for value in geometry(core)['breaks']:
            if 0.<value<R:cuts.add(power(value/R,k))
    cuts=sorted(cuts);result['cuts']=cuts
    inverse=1./k;c_open=c_under=0.
    for u0,u1 in zip(cuts,cuts[1:]):
        if u1-u0<=1e-15:continue
        mid,half=(u0+u1)/2.,(u1-u0)/2.
        for gx,gw in nodes():
            weight=n.number(gw)*half/n.number(n.TAU);rho=R*power(mid+half*n.number(gx),inverse);covered=[];result['nodes']+=1
            for i in near:
                arcs=geometry(targets[i],rho)['arcs']
                if arcs:
                    front[i]+=weight*aim._measure(aim._subtract(arcs,covered));covered=aim._union(covered,arcs)
                if grow>0:reach[i]+=weight*aim._measure(geometry(targets[i],rho,grow)['arcs'])
            if use_core:
                arcs=geometry(core,rho)['arcs']
                if arcs:
                    c_under+=weight*aim._measure(arcs);c_open+=weight*aim._measure(aim._subtract(arcs,covered))
    clip=lambda value:min(1.,max(0.,value))
    finite(*front,*reach,c_open,c_under)
    result.update(front=list(map(clip,front)),reach=list(map(clip,reach)),core_open=clip(c_open),core_under=clip(c_under));return result

def prepared_cache(shape_values,aim):
    from coordinate_geometry_reference import rotation,rotation_radians,norm
    kind,x,y,r,w,h,rot=shape_values;ax,ay=aim;dx,dy=ax-x,ay-y;cx,cy=x-ax,y-ay
    co,si=(1.,0.) if kind==1 else rotation(rot)
    lx,ly=dx*co+dy*si,-dx*si+dy*co;hw,hh=w/2.,h/2.
    return [cx,cy,lx,ly,hw,hh,rotation_radians(rot),norm(cx,cy),*(norm(sx*hw-lx,sy*hh-ly) for sx,sy in [(1,1),(-1,1),(1,-1),(-1,-1)])]
