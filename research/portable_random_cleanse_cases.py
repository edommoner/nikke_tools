"""Literal harmful-recipient pools and per-actor removal witnesses."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(ammo()[0]);base.pop('contract');rows=[]
    def add(label,pool,picked,*,targets=(),immutable=(),value=1,second=False,seed=19,owner=0):
        c=copy.deepcopy(base);c.update(name='random-cleanse-'+label,seed=seed,effects=[],owners=[])
        names=roster_names(c)
        def mark(name,slots,polarity):
            if not slots:return
            c['effects'].append(field('def_pct',-10,[names[i] for i in slots],name,polarity=polarity));c['owners'].append(owner)
        mark('first',targets,'harmful')
        if second:mark('second',targets,'harmful')
        mark('locked',immutable,'harmful_irremovable')
        mark('beneficial',range(5),'beneficial')
        c['effects'].append(instant('debuff_cleanse',value,'allies_random_with_debuff:2','random-cleanse'));c['owners'].append(owner)
        after={}
        for name,slots in [('first',targets),('second',targets if second else ()),('locked',immutable),('beneficial',range(5))]:
            # Canonical positive fractions truncate but remove at least one.
            removed=picked if name=='first' or (name=='second' and (value<=0 or int(value)>=2)) else []
            remaining=[i for i in slots if i not in removed]
            if remaining:after[name]=remaining
        before={e['name']:[names.index(n) for n in e['target']] for e in c['effects'][:-1]}
        c['contract']=dict(pool=pool,picked=picked,owner=owner,before=before,remaining=after)
        rows.append(c);return c
    add('empty',[],[])
    add('self-included',[0],[0],targets=[0])
    add('other-singleton',[4],[4],targets=[4])
    add('irremovable-eligible',[4],[4],immutable=[4])
    add('self-and-other',[0,4],[0,4],targets=[0,4])
    add('removable-and-locked',[1,2,3,4],[1,3],targets=[1,2],immutable=[3,4])
    add('shared-partial-strip',list(range(5)),[0,4],targets=list(range(5)))
    add('oldest-per-actor',list(range(5)),[0,4],targets=list(range(5)),second=True)
    add('zero-unlimited',list(range(5)),[0,4],targets=list(range(5)),second=True,value=0)
    add('negative-unlimited',list(range(5)),[0,4],targets=list(range(5)),second=True,value=-.5)
    add('positive-subunit-removes-one',list(range(5)),[0,4],targets=list(range(5)),second=True,value=.5)
    add('fraction-truncates',list(range(5)),[0,4],targets=list(range(5)),second=True,value=1.9)
    add('seed-zero',list(range(5)),[3,4],targets=list(range(5)),seed=0)
    add('last-caster-included',[4],[4],targets=[4],owner=4)
    add('two-per-actor',list(range(5)),[0,4],targets=list(range(5)),second=True,value=2)
    add('huge-finite-limit',list(range(5)),[0,4],targets=list(range(5)),second=True,value=1e308)
    add('next-below-two',list(range(5)),[0,4],targets=list(range(5)),second=True,value=1.9999999999999998)
    add('smallest-positive-removes-one',list(range(5)),[0,4],targets=list(range(5)),second=True,value=5e-324)
    return rows
