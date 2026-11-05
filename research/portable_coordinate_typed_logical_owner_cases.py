"""Full Prim definitions with explicitly declared ADD-owned typed targets."""
import copy
from portable_coordinate_typed_owner_cases import fixtures as original,prepare as owner_prepare
from coordinate_typed_actor_policy import LOGICAL_FIELD_MODE

def fixtures():
    rows=[]
    for name,kind,dead in [('hp-add-owner',3,False),('projectile-add-owner',2,False),('hp-dead-add-owner',3,True)]:
        c=copy.deepcopy(original()[-1]);c['name']='coordinate-typed-logical-owner/'+name
        c['typed_actor_policy']={'mode':LOGICAL_FIELD_MODE}
        for binding in c['typed_bindings']:binding.update(kind=kind,owner=[5,1,1])
        if dead:c['typed_bindings'][0]['capacity']=1.
        marker,field=c['declared_owner_counter'];marker['target_counter']['actor']['kind']='projectile' if kind==2 else 'hp_shield'
        field['trigger']['condition']=['target_is_add']
        c['logical_owner_contract']=dict(kind=kind,owner=[5,1,1],dead=dead)
        rows.append(c)
    return rows

def prepare(row):
    c,p=owner_prepare(row);c['logical_owner_contract']=copy.deepcopy(row['logical_owner_contract']);return c,p
