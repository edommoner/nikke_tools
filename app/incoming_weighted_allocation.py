"""Declared frozen incoming allocation; not inferred Bay game constants.

The caller snapshots living body receivers and the independent caster cover.
This module does not select carriers, apply protection or emit hit callbacks.
Divide weight by the ordered denominator, then multiply incoming quantity.
No integer rounding, one-point floor or residual assignment is introduced.
"""
import math


def allocate(amount, body_mask, caster, caster_weight, other_weight, cover_weight, cover_active):
    if type(body_mask) is not int or not 1 <= body_mask <= 31:
        raise ValueError('Nonempty frozen five-body live mask required')
    if type(caster) is not int or not 0 <= caster < 5 or type(cover_active) is not bool:
        raise ValueError('Original caster slot and explicit cover state required')
    if cover_active and not body_mask & (1 << caster):
        raise ValueError('Independent cover requires its living original owner')
    quantities=(amount,caster_weight,other_weight,cover_weight)
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in quantities):
        raise ValueError('Finite explicit incoming quantity and weights required')
    if amount < 0 or min(caster_weight,other_weight,cover_weight) <= 0:
        raise ValueError('Nonnegative incoming quantity and positive explicit weights required')
    active_mask=body_mask | (32 if cover_active else 0)
    weights=[caster_weight if who==caster else other_weight for who in range(5)]+[cover_weight]
    total=0.0
    for who,weight in enumerate(weights):
        if active_mask & (1 << who): total += weight
    if not math.isfinite(total): return dict(status=16,active_mask=active_mask,total=None,shares=None)
    shares=[amount*(weight/total) if active_mask & (1 << who) else 0.0 for who,weight in enumerate(weights)]
    if not all(map(math.isfinite,shares)): return dict(status=16,active_mask=active_mask,total=None,shares=None)
    return dict(status=0,active_mask=active_mask,total=total,shares=shares)
