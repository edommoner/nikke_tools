"""Resource consumption quantities, separate from charge caps and hit events."""
import math

RESOURCE_MARKERS=frozenset({'gauge_charge_enabled'})

def resource_marker(effect):
    """A named carrier associated with a resource; it does not intercept charges."""
    if effect.get('stat') not in RESOURCE_MARKERS:return None
    if effect.get('type')!='buff' or effect.get('target','self')!='self' or not isinstance(effect.get('name'),str) or not effect['name']:
        raise ValueError('Resource marker requires a named self state')
    identifier=effect.get('gauge_id')
    if not isinstance(identifier,str) or not identifier or effect.get('max_stack',1)!=1:
        raise ValueError('Invalid resource marker association')
    if any(key in effect for key in ('gauge_max','fixed_value','values','scaling','scaling_ref','minimum_remaining','hit_count_gauge_ref')):
        raise ValueError('Resource marker cannot modify a numeric quantity')
    return identifier


def minimum_remaining(effect):
    if 'minimum_remaining' not in effect:
        return 0.0
    if effect.get('type') != 'instant' or effect.get('stat') not in ('gauge_consume', 'gauge_consume_as_ammo'):
        raise ValueError('A consumption minimum requires a gauge-consume operation')
    value = effect['minimum_remaining']
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1e30:
        raise ValueError('Invalid resource-consumption minimum')
    return float(value)


def consume_resource(current, requested, minimum=0.0):
    """Return remaining quantity and actual spend, without delivering events.

    Compute spend from requested/available quantities, not subtraction of the
    rounded remainder. That distinction preserves integer event boundaries.
    -1 consumes everything available above this operation's minimum.
    """
    for value in (current, requested, minimum):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('Resource quantities must be finite numbers')
    if not 0 <= minimum <= 1e30:
        raise ValueError('Invalid resource-consumption minimum')
    available = max(0.0, current - minimum)
    after = minimum if requested == -1 else max(minimum, current - requested)
    spent = available if requested == -1 else max(0.0, min(requested, available))
    return after, spent
