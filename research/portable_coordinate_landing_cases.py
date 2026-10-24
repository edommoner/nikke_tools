"""Authored expected-mode geometry, never precalculated probabilities/cuts."""
def circle(x,y,r):return (1,float(x),float(y),float(r),0.,0.,0.)
def rect(x,y,w,h,rot=0.):return (2,float(x),float(y),0.,float(w),float(h),float(rot))
def fixtures():
    out=[]
    def add(name,targets=(),core=None,aim=(0.,0.),radius=3.,grow=0.,k=2.55):out.append((name,dict(targets=list(targets),core=core,aim=aim,radius=radius,grow=grow,k=k)))
    add('empty');add('far',(circle(100,100,1),),circle(100,-100,1))
    for k in [.5,1.,2.,2.55,4.,2.**-16,65536.]:add('center-core/'+str(k),core=circle(0,0,1),radius=2.,k=k)
    add('full-core',core=circle(0,0,5),radius=2.)
    add('center-target',(circle(0,0,1),),radius=2.)
    add('covered-core',(circle(0,0,1),),circle(0,0,.5),radius=2.)
    add('full-cover',(circle(0,0,5),),circle(0,0,2),radius=2.,grow=.5)
    for kind,shape in [('circle',circle(.7,.3,.8)),('rectangle',rect(.5,-.3,2,1,45)),('negative-rotation',rect(-.2,.5,1,2,-450))]:
        for grow in [0.,.5]:add(f'{kind}/grow-{grow}',(shape,),circle(.2,.1,.7),grow=grow)
    pair=[circle(.5,0,1.1),rect(-.4,.2,1.6,1.2,30)]
    add('depth-forward',pair,circle(0,0,.9),grow=.3);add('depth-reversed',list(reversed(pair)),circle(0,0,.9),grow=.3)
    add('three-overlapping',(*pair,circle(0,-.8,1.3)),circle(.2,.1,.7),grow=.7)
    add('far-target-center-core',(rect(100,100,1,1),),circle(0,0,1),radius=2.)
    add('translated',tuple((s[0],s[1]+10,s[2]-20,*s[3:]) for s in pair),circle(10,-20,.9),aim=(10.,-20.),grow=.3)
    add('negative-radius-clamp',(circle(0,0,2e-9),),radius=-1.)
    add('maximum-target-count',tuple(circle(0,0,1) for _ in range(127)),radius=2.)
    return out
