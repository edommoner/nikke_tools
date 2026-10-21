"""Read native storage objects only; no capacity or healing reconstruction."""
import math


def before_finish(manager,names):
    rows=[]
    for ab in manager._active:
        if ab.effect.get('stat')!='heal_overcharge_store':continue
        current=getattr(ab,'heal_store_current',{})
        capacity=getattr(ab,'heal_store_capacity',{})
        rows.append(dict(row=ab.effect['_portable_observer_row'],owner=names.index(ab.caster),
                         activated=ab.activated_at,end=1e30 if math.isinf(ab.expires_at) else ab.expires_at,
                         initialized=hasattr(ab,'heal_store_current'),
                         recipients=sorted(names.index(n) for n in capacity),
                         current=[current.get(n,0.0) for n in names],
                         capacity=[capacity.get(n,0.0) for n in names]))
    return sorted(rows,key=lambda r:(r['row'],r['recipients']))
