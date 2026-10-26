"""Actual finite-HP ADD kills, keeping the original full Prim battle."""
import copy
from portable_coordinate_typed_logical_owner_cases import fixtures as original,prepare as logical_prepare

def fixtures():
    rows=[]
    for label,hp,capacity,late in (
        ('same-packet-after-child',1.,1.,False),
        ('dead-before-late-child',1.,1e30,True),
        ('visible-field-before-later-death',1e6,1.,False),
    ):
        c=copy.deepcopy(original()[0]);c['name']='coordinate-typed-owner-hp-death/'+label
        node=next(p for p in c['patterns'] if p['id']=='owner-adds');node['spec']['hp']=hp
        c['typed_bindings'][0]['capacity']=capacity
        if late:
            marker=c['declared_owner_counter'][0];marker['trigger']['timing']=['every:1.25s'];marker['max_trigger']=1
        c['owner_hp_death']=dict(hp=hp,late=late,visible_before_death=hp>1.,owner=[5,1,1])
        rows.append(c)
    return rows

def prepare(row):
    c,p=logical_prepare(row);c['owner_hp_death']=copy.deepcopy(row['owner_hp_death']);return c,p
