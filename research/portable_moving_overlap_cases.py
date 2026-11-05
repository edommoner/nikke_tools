"""Unmodified Yuni, Yan and Nihilister effects in one moving-target battle."""
import copy
from portable_moving_typed_cases import fixtures as typed_cases,prepare
from portable_original_identity_inventory import selected_profile_bodies


def fixtures():
    source=next(body for name,stage,body in selected_profile_bodies(['니힐리스타'],0))
    rows=[]
    for index in (3,4):
        row=copy.deepcopy(typed_cases()[index]);body=row['body']
        body['squad']=['니힐리스타' if name=='N102' else name for name in body['squad']]
        del body['profile']['chars']['N102']
        body['profile']['chars']['니힐리스타']=copy.deepcopy(source['profile']['chars']['니힐리스타'])
        row['name']='moving-overlap/'+row['contract']['scenario']
        for collider in row['logical_geometry']:collider['shape'].update(x=-60.,r=100.)
        row['typed_geometry']['shapes'][0].update(x=-50.,y=0.,r=30.)
        row['group_contract']=dict(owner='니힐리스타',child='버닝 샷 3',outside=False)
        rows.append(row)
    return rows


def prepare_case(row):
    case,prepared=prepare(row)
    case['group_contract']=copy.deepcopy(row['group_contract'])
    return case,prepared


def verify(case,native):
    from portable_moving_group_contracts import verify as group_contract
    result=group_contract(case,native)
    fields=[s for f in native['enemy_movement']['frames'] for s in f['segments']]
    overlap=[s for s in fields if s['disabled'] and s['forced']]
    assert overlap,'Both original movement carriers must overlap in a live battle'
    assert {'enemy_movement_disable','force_move'} <= {e['stat'] for s in overlap for e in s['fields']}
    precedence=case['enemy_movement']['precedence']
    for segment in overlap:
        expected=segment['before'] if precedence=='disable-before-force' else [0.,0.]
        assert segment['after']==expected,'Declared simultaneous-carrier precedence'
    result.update(overlap_segments=len(overlap),precedence=precedence,
        original_operators=['enemy_movement_disable','force_move'],
        in_game_precedence_verified=False)
    return result
