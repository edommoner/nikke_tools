"""Explicit deterministic geometry profile; historical host Shape is untouched."""
import math
import portable_coordinate_numeric_v1 as n
from portable_coordinate_math_cases import compatible_bits

def norm(x,y):return n.number(compatible_bits(n.bits(x),n.bits(y)))
def finite(*values):
    if not all(math.isfinite(v) for v in values):raise ValueError('Nonfinite geometry intermediate')
def rotation(degrees):
    s,c=n.sincos_degrees(n.bits(degrees));return n.number(c),n.number(s)
def rotation_radians(degrees):
    magnitude=n.positive_remainder(n.bits(degrees));return n.number(n.mul(magnitude,n.DEG_RAD)^(n.bits(degrees)&n.SIGN))
def circle(cx,cy,r,rho,aim):
    d=norm(cx,cy);finite(d,d+rho,d+r,d-r)
    if rho<=0:return [(0.,n.number(n.TAU))] if d<=r else []
    if d+rho<=r:return [(0.,n.number(n.TAU))]
    if rho>=d+r or rho<=d-r:return []
    top=rho*rho+d*d-r*r;bottom=2.*rho*d;finite(top,bottom)
    if bottom==0:raise ValueError('Underflowed geometry denominator')
    c=top/bottom;finite(c);half=n.number(n.acos_bits(n.bits(max(-1.,min(1.,c)))))
    return aim._arc(n.number(n.atan2_bits(n.bits(cy),n.bits(cx)))-half,2.*half)
def halfplane(beta,c,rho,aim):
    finite(c)
    if rho<=0:return [(0.,n.number(n.TAU))] if c>=0 else []
    s=c/rho;finite(s)
    if s>=1:return [(0.,n.number(n.TAU))]
    if s<=-1:return []
    a=n.number(n.acos_bits(n.bits(s)));return aim._arc(beta+a,n.number(n.TAU)-2.*a)
def rectangle(lx,ly,hw,hh,rho,aim):
    out=halfplane(0.,hw-lx,rho,aim)
    for beta,c in [(n.number(n.PI),hw+lx),(n.number(n.HALF_PI),hh-ly),(-n.number(n.HALF_PI),hh+ly)]:
        if not out:return []
        out=aim._intersect(out,halfplane(beta,c,rho,aim))
    return out

def evaluate(values):
    # Input is static shape kind plus ten authored scalar values.
    import engine_worker
    from calculator import aim
    kind,x,y,r,w,h,rot,ax,ay,rho,grow=values
    finite(x,y,r,w,h,rot,ax,ay,rho,grow)
    if kind not in (1,2) or grow<0 or rho<0:raise ValueError('Invalid geometry shape/domain')
    if kind==1 and not (r>0 and w==h==0) or kind==2 and not (r==0 and w>0 and h>0):raise ValueError('Invalid shape dimensions')
    co,si=(1.,0.) if kind==1 else rotation(rot)
    dx,dy=ax-x,ay-y;finite(dx,dy)
    if kind==1:
        d=norm(dx,dy);distance=max(0.,d-r);radius=r+grow;finite(d,distance,radius)
        arcs=circle(x-ax,y-ay,radius,rho,aim);breaks=[abs(d-radius),d+radius]
    else:
        lx,ly=dx*co+dy*si,-dx*si+dy*co;hw,hh=w/2.,h/2.;finite(lx,ly,hw+grow,hh+grow)
        distance=norm(max(abs(lx)-hw,0.),max(abs(ly)-hh,0.));finite(distance)
        arcs=rectangle(lx,ly,hw+grow,hh,rho,aim)
        if grow>0:
            arcs=aim._union(arcs,rectangle(lx,ly,hw,hh+grow,rho,aim))
            for cx,cy in [(hw,hh),(-hw,hh),(hw,-hh),(-hw,-hh)]:arcs=aim._union(arcs,circle(cx-lx,cy-ly,grow,rho,aim))
        if rot:arcs=aim._shift(arcs,rotation_radians(rot))
        breaks=[]
        for ew,eh in [(hw+grow,hh),(hw,hh+grow)]:
            breaks.extend([abs(ew-lx),abs(ew+lx),abs(eh-ly),abs(eh+ly)])
            breaks.extend(norm(sx*ew-lx,sy*eh-ly) for sx in (1,-1) for sy in (1,-1))
        if grow>0:
            for sx in (1,-1):
                for sy in (1,-1):
                    d=norm(sx*hw-lx,sy*hh-ly);breaks.extend([abs(d-grow),d+grow])
    finite(*breaks,*(v for pair in arcs for v in pair));measure=aim._measure(arcs)
    return dict(reference_kind='deterministic-common-cpu',contract=n.PROFILE,distance=distance,contains=distance<=grow+1e-9,cosine=co,sine=si,arcs=arcs,breaks=breaks,measure=measure)
