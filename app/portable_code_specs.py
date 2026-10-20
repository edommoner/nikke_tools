"""Immutable authored enemy-code IDs; equality is evaluated on the GPU."""
TARGET_CODE = 44
PREFIX = 'target_code:'

def code_names(effects, enemy_code, states, capacity):
    if enemy_code is not None and not isinstance(enemy_code,str):
        raise ValueError('Enemy code must be a string or null')
    required=[c[len(PREFIX):] for effect,_ in effects for c in effect.get('trigger',{}).get('condition',[]) if c.startswith(PREFIX)]
    if not required:return 0,0
    for name in required + ([enemy_code] if enemy_code else []):
        states.setdefault(name,len(states))
    if len(states)>capacity:raise ValueError('Enemy-code reference capacity exceeded')
    return states[enemy_code]+1 if enemy_code else 0,len(states)

def condition_id(condition, states):
    return states[condition[len(PREFIX):]]+1
