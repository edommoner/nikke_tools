"""Use the existing physical/movement native executor unchanged."""
from portable_moving_group_cases import prepare_case
from world_moving_typed_native import observe as physical

def observe(row):
    case=row if 'original_run' in row else prepare_case(row)[0]
    return physical(case)
