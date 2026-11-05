"""Explicit canonical aim-to-enemy routing for ordinary current damage.

Typed objects remain physical interception recipients. This policy delegates
ordinary damage's logical enemy selection to the unchanged canonical resolver.
Enemy field/mutation inheritance still requires a separate ownership contract.
"""
from enemy_recipient_specs import CURRENT_TARGETS
MODE='canonical-current-damage-v1'
FIELD_MODE='body-owned-current-fields-v1'
LOGICAL_FIELD_MODE='logical-owned-current-fields-v1'

def owns_fields(policy):return policy in ({'mode':FIELD_MODE},{'mode':LOGICAL_FIELD_MODE})

def validate_bindings(policy,bindings):
    if not owns_fields(policy):return
    if policy=={'mode':FIELD_MODE}:
        if not bindings or any(b.get('kind') not in (2,3) or b.get('owner')!=[0,0,1] for b in bindings):raise ValueError('Typed field policy requires explicit BODY-owned projectile/HP shield bindings')
        return
    from impact_specs import ActorHandle,ActorKind
    if not bindings:raise ValueError('Typed field policy requires explicit logical owner bindings')
    for binding in bindings:
        owner=binding.get('owner')
        if binding.get('kind') not in (2,3) or not isinstance(owner,list) or len(owner)!=3:raise ValueError('Typed field requires an explicit logical owner')
        handle=ActorHandle(*owner)
        if handle.kind not in (ActorKind.BODY,ActorKind.ADD) or handle.kind==ActorKind.BODY and owner!=[0,0,1]:raise ValueError('Typed field owner must be BODY or an exact ADD generation')

def normalize(policy):
    if not isinstance(policy,dict) or set(policy)!={'mode'} or policy.get('mode') not in (MODE,FIELD_MODE,LOGICAL_FIELD_MODE):raise ValueError('Explicit canonical current-damage actor policy required')
    return dict(policy)

def validate_effects(effects,policy):
    if policy is not None:normalize(policy)
    for effect in effects:
        target=effect.get('target')
        current=any(isinstance(t,str) and t in CURRENT_TARGETS for t in target) if isinstance(target,list) else isinstance(target,str) and target in CURRENT_TARGETS
        if not current:continue
        if policy is None:raise ValueError('Typed aim logical enemy recipient requires its own actor policy')
        if effect.get('type')!='damage' and not owns_fields(policy):raise ValueError('Typed current enemy fields/mutations require an ownership policy')
