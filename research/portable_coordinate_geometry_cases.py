"""Literal shape/aim/ring inputs. No geometric or transcendental evaluation."""
import random,sys

def fixtures():
    rows=[]
    shapes=[(1,0.,0.,2.,0.,0.,0.),(1,3.,-2.,1.,0.,0.,45.),(1,-4.,3.,4.,0.,0.,0.)]
    shapes += [(2,1.,-2.,0.,6.,2.,angle) for angle in (0.,45.,-45.,90.,180.,270.,360.,450.,-450.,1e300,sys.float_info.max,5e-324)]
    for i,shape in enumerate(shapes):
        for j,(ax,ay) in enumerate([(0.,0.),(1.,-2.),(3.,-1.),(10.,10.)]):
            for k,rho in enumerate([0.,.25,1.,2.,5.,20.]):
                for g,grow in enumerate([0.,.5,2.]):rows.append((f'shape/{i}/{j}/{k}/{g}',(*shape,ax,ay,rho,grow)))
    rng=random.Random(0x43475631)
    for i in range(128):
        kind=1 if i%3==0 else 2;x=rng.uniform(-10,10);y=rng.uniform(-10,10)
        r=rng.uniform(.1,8) if kind==1 else 0.;w=0. if kind==1 else rng.uniform(.1,10);h=0. if kind==1 else rng.uniform(.1,10)
        rows.append((f'random/{i}',(kind,x,y,r,w,h,rng.uniform(-720,720),rng.uniform(-10,10),rng.uniform(-10,10),rng.uniform(.01,20),rng.uniform(0,5))))
    # Decision-changing host-trig boundary is now authored angle only.
    rows.append(('contains/sin45-boundary',(2,0.,0.,0.,2.,2.,45.,1.4142135637873085,0.,1.,0.)))
    return rows
