"""Explicit canonical aim-to-enemy routing for ordinary current damage.

Typed objects remain physical interception recipients. This policy delegates
ordinary damage's logical enemy selection to the unchanged canonical resolver.
Enemy field/mutation inheritance still requires a separate ownership contract.
"""
from enemy_recipient_specs import CURRENT_TARGETS
MODE='canonical-current-damage-v1'

def normalize(policy):
    if not isinstance(policy,dict) or policy!={'mode':MODE}:raise ValueError('Explicit canonical current-damage actor policy required')
    return dict(policy)

def validate_effects(effects,policy):
    if policy is not None:normalize(policy)
    for effect in effects:
        if effect.get('target') not in CURRENT_TARGETS:continue
        if policy is None:raise ValueError('Typed aim logical enemy recipient requires its own actor policy')
        if effect.get('type')!='damage':raise ValueError('Typed current enemy fields/mutations require an ownership policy')
