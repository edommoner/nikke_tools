"""Authored sampler inputs, never CPU-generated random samples or point tables."""
def fixtures():
    rows=[]
    def add(name,**kw):
        rows.append(dict(name=name,seed=19,mode=2,count=16,skip=0,bound=0,critical=1,aim=[1.,-2.],radius=16.,k=2.55)|kw)
    for seed in (0,1,19,2**32+1,2**64-1):
        for mode in (0,1,2):
            for skip in (0,623,624,1247):add(f'seed-{seed}/mode-{mode}/skip-{skip}',seed=seed,mode=mode,skip=skip)
    for bound in (1,3,5,7,31,65,127,128):add('interleave-target-'+str(bound),bound=bound,skip=623)
    for radius in (-10.,-0.,0.,1e-200,1e-9,1e-8,1e100,1e300):
        for mode in (0,1):add(f'radius-{radius!r}/mode-{mode}',radius=radius,mode=mode,critical=0,count=4)
    for k in (2.**-16,.5,1.,2.,2.55,65536.):add('exponent-'+str(k),k=k,skip=624)
    for ax,ay in [(0.,-0.),(-1e200,1e200),(1e-300,-1e-300)]:add(f'aim-{ax!r}-{ay!r}',aim=[ax,ay])
    return rows
