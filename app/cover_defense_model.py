"""Declared independent cover DEF; no inferred game level curve or admission."""
import math

def effective_cover_defense(base,percentage):
    return base*(1.0+percentage/100.0)

def incoming_damage(attack,coefficient,defense,received):
    amount=max(attack-defense,0.0)*coefficient/100.0
    amount=amount*max(0.0,1.0+received/100.0)
    return max(amount,1.0)

def numeric(attack,coefficient,cover_base,cover_percentage,received,body_defense):
    values=(attack,coefficient,cover_base,cover_percentage,received,body_defense)
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in values) or min(attack,coefficient,cover_base)<0:
        raise ValueError('Finite declared quantities and nonnegative attack/coefficient/cover base required')
    defense=effective_cover_defense(cover_base,cover_percentage)
    cover=incoming_damage(attack,coefficient,defense,received)
    body=incoming_damage(attack,coefficient,body_defense,received)
    if not all(map(math.isfinite,(defense,cover,body))):return dict(status=16,values=None)
    return dict(status=0,values=[defense,cover,body])

def live_defense(manager,name,t,base):
    """Use existing ordered carrier/value semantics, never the owner's body DEF."""
    if type(base) not in (int,float) or not math.isfinite(base) or base<0:raise ValueError('Explicit independent cover base DEF required')
    value=effective_cover_defense(base,manager._live_sum(name,'cover_def_pct',t))
    if not math.isfinite(value):raise OverflowError('Nonfinite declared cover DEF')
    return value
