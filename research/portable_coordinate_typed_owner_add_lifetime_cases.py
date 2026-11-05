"""Full Prim definitions and direct ADD ownership across actual graph lifetimes."""
import copy
from portable_coordinate_typed_logical_owner_cases import fixtures as original,prepare as logical_prepare

def fixtures():
    rows=[]
    for label,kind,until,repeat,owner_gen,late in (
        ('owner-dead-before-child',3,.5,1,1,True),
        ('owner-dies-after-child',2,1.,1,1,False),
        ('old-field-not-inherited-on-respawn',3,1.,0,1,False),
        ('second-generation-owner',2,1.,0,2,True),
    ):
        c=copy.deepcopy(original()[0 if kind==3 else 1]);c['name']='coordinate-typed-owner-add-lifetime/'+label
        node=next(p for p in c['patterns'] if p['id']=='owner-adds');node.update(until=dict(time=until),repeat=repeat)
        if repeat!=1:node['after']=['start',node['id']]
        for b in c['typed_bindings']:b['owner']=[5,1,owner_gen]
        c['logical_owner_contract']['owner']=[5,1,owner_gen]
        if late:
            c['declared_owner_counter'][0]['trigger']['timing']=['every:1.25s']
            c['declared_owner_counter'][0]['max_trigger']=1
        c['owner_add_lifetime']=dict(kind=kind,owner_generation=owner_gen,repeat=repeat,until=until,late=late,dead_before_child=label=='owner-dead-before-child')
        rows.append(c)
    return rows

def prepare(row):
    c,p=logical_prepare(row);c['owner_add_lifetime']=copy.deepcopy(row['owner_add_lifetime']);return c,p
