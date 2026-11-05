"""Presence-only element advantage; roster element identities remain immutable."""
STAT=88

def enabled(effect):return effect.get('type')=='buff' and effect.get('stat')=='element_code_override'

def validate(effect):
    if not enabled(effect):return
    if effect.get('target_code') is not None and not isinstance(effect['target_code'],str):raise ValueError('Element override target_code must be a string or null')
    if effect.get('scaling') is not None:raise ValueError('Element override has no numeric scaling')

def code_tag(effect,states):
    code=effect.get('target_code');return 0 if code is None else states[code]+1

def legacy_effect(effect):
    if not enabled(effect):return effect
    return dict((key,value) for key,value in dict(effect,stat='').items() if key!='target_code')
