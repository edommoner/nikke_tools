"""Data-only BODY-owned projectile, death and exact-generation contracts."""
import copy
from portable_coordinate_typed_owner_cases import fixtures as original,prepare as owner_prepare

def fixtures():
    rows=[]
    specs=[('projectile-live',2,False,1,False),('hp-dead',3,True,1,False),('projectile-dead',2,True,1,False),('hp-generation2',3,False,2,False),('projectile-generation2',2,False,2,False),('hp-stale-filter',3,False,1,True),('projectile-stale-filter',2,False,1,True)]
    for label,kind,dead,generation,stale in specs:
        c=copy.deepcopy(original()[-1]);c['name']='coordinate-typed-owner-lifecycle/'+label
        for b in c['typed_bindings']:b['kind']=kind
        if dead:c['typed_bindings'][0]['capacity']=1.
        marker=c['declared_owner_counter'][0];marker['target_counter']['actor']=dict(kind='projectile' if kind==2 else 'hp_shield',identity=10,generation=generation)
        if generation==2 or stale:
            node=c['patterns'][0];node.update(after=['start',node['id']],until=dict(time=.5),repeat=4)
        if stale:marker['trigger']['timing']=['every:1.25s']
        c['body']['enemy']['patterns']=copy.deepcopy(c['patterns'][:1])
        c['owner_lifecycle']=dict(kind=kind,generation=generation,dead_query=dead,stale_filter=stale,manual=False)
        rows.append(c)
    c=copy.deepcopy(original()[3]);c['name']='coordinate-typed-owner-lifecycle/projectile-manual'
    for b in c['typed_bindings']:b['kind']=2
    c['owner_lifecycle']=dict(kind=2,generation=1,dead_query=False,stale_filter=False,manual=True);rows.append(c)
    return rows

def prepare(row):
    c,p=owner_prepare(row);c['owner_lifecycle']=copy.deepcopy(row['owner_lifecycle']);return c,p
