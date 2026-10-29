"""All 127 ADD slots at full duration, retaining original movement/group skills."""
import copy
from portable_moving_group_cases import fixtures as groups,prepare_case

def fixtures():
    from calculator.boss_pattern import validate
    from world_actor_specs import bindings
    row=copy.deepcopy(groups()[0]);row['name']='moving-many/127-adds-30-seconds'
    row['patterns'][0]['spec']['count']=127
    row['body']['enemy']['patterns']=copy.deepcopy(row['patterns'])
    actors=[b for b in bindings(validate(row['patterns'],coord=True)) if int(b.kind)==5]
    shape=row['logical_geometry'][0]['shape'];rule=row['enemy_movement']['actors'][0]
    row['logical_geometry']=[dict(label=b.label,shape=dict(shape,x=-60. if i<2 else 10000.+i,z=float(i+1))) for i,b in enumerate(actors)]
    row['enemy_movement']['actors']=[dict(copy.deepcopy(rule),label=b.label) for b in actors]
    row['typed_attachment']['bindings'][0]['actor_label']=actors[0].label
    row['typed_bindings'][0]['owner']=[5,actors[0].identity,1]
    return [row]
