"""All five-body survivor sets and independent cover snapshots, inputs only."""
def fixtures():
    rows=[]
    def add(label,amount,mask,caster,self_weight,other_weight,cover_weight,cover):
        rows.append(dict(name='weighted-incoming/'+label,args=[amount,mask,caster,self_weight,other_weight,cover_weight,cover]))
    for mask in range(1,32):
        for caster in range(5):
            for cover in (False,True):
                if cover and not mask&(1<<caster):continue
                for amount in (0.,1.,123456.789,1e308,5e-324):
                    add(f'survivors/{mask}/{caster}/{int(cover)}/{amount.hex()}',amount,mask,caster,8.,3.,262.,cover)
    # Explicit non-Bay values prevent accidental hard-coded rounded ratios.
    for i,weights in enumerate(((1.,1.,1.),(.125,1.75,9.5),(1e-300,1e-300,1e-300),(1e308,1e308,1e308))):
        add(f'weights/{i}',98765.4321,31,2,*weights,True)
    return rows
