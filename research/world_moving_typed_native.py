"""Complete original native chain with one logical/typed pellet and clock."""
from coordinate_moving_typed_geometry import moving_typed_geometry
from world_coordinate_typed_owner_native import observe as original
from portable_moving_typed_cases import prepare

def observe(row):
    case=row if 'original_run' in row else prepare(row)[0]
    with moving_typed_geometry(case['logical_geometry'],case['enemy_movement'],case['typed_attachment']) as runtime:
        native,trace=original(case)
    native['enemy_movement']=runtime['movement']
    native['logical_geometry']={k:runtime['logical_geometry'][k] for k in ('shots','packets','pellets')}
    native['typed_attachments']=runtime['typed_attachments']
    return native,trace
