"""Original Yuni movement and Nihilister group consumer, without new effects."""
import copy
from portable_moving_typed_cases import fixtures as typed_cases,prepare
from portable_original_identity_inventory import selected_profile_bodies

def fixtures():
    source=next(b for n,s,b in selected_profile_bodies(['니힐리스타'],0))
    rows=[]
    for label,index,outside in [('moving-hit',0,False),('outside-control',0,True),('renewed-owner',2,False)]:
        row=copy.deepcopy(typed_cases()[index]);body=row['body']
        body['squad']=['니힐리스타' if n=='미란다' else n for n in body['squad']]
        del body['profile']['chars']['미란다']
        body['profile']['chars']['니힐리스타']=copy.deepcopy(source['profile']['chars']['니힐리스타'])
        row['name']='moving-group/'+label
        for collider in row['logical_geometry']:
            collider['shape'].update(x=10000. if outside else -60.,r=100.)
        row['typed_geometry']['shapes'][0].update(x=10000. if outside else -50.,y=0.,r=30.)
        row['group_contract']=dict(owner='니힐리스타',child='버닝 샷 3',outside=outside)
        rows.append(row)
    return rows

def prepare_case(row):
    case,prepared=prepare(row)
    case['group_contract']=copy.deepcopy(row['group_contract'])
    return case,prepared
