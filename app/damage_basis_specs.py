"""Per-skill attack basis; independent of hit-count/coefficient references."""
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class DamageBasis:
    mode:int=0 # 0 ordinary, 1 add current maximum HP to flat ATK, 2 replace ATK
    hp_pct:float=0

def damage_basis(effect):
    scaling=effect.get('scaling')
    modes={'max_hp_additive':1,'max_hp_replacement':2}
    mode=modes.get(scaling,0) if isinstance(scaling,str) else 0
    if not mode:
        if 'scaling_hp_pct' in effect:raise ValueError('HP attack basis requires an explicit scaling mode')
        return DamageBasis()
    if effect.get('type')!='damage':raise ValueError('HP attack basis requires damage')
    value=effect.get('scaling_hp_pct')
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1000000:
        raise ValueError('Invalid HP attack-basis percentage')
    if 'scaling_ref' in effect:raise ValueError('HP attack basis cannot also scale the coefficient by a state reference')
    return DamageBasis(mode,float(value))
