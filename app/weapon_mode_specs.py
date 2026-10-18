"""Declarative weapon-mode commands, independent of character identity."""
import math
TOGGLE_FLAG=128
AMMO_EQUIVALENT=37
MAX_AMMO_EQUIVALENT=4096

def toggle_flag(effect):
    if 'toggle' not in effect:return 0
    if effect.get('type')!='weapon_change' or type(effect['toggle']) is not bool:
        raise ValueError('Toggle requires a boolean weapon-mode flag')
    if effect['toggle'] and (not isinstance(effect.get('name'),str) or not effect['name']):
        raise ValueError('Toggle requires a nonempty weapon-mode name')
    return TOGGLE_FLAG if effect['toggle'] else 0

def extra_ammo_count(value):
    """The real shot accounts for one round; only append the N-1 notices."""
    if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>MAX_AMMO_EQUIVALENT:
        raise ValueError('Ammo-equivalent count exceeds the bounded notification program')
    return max(0,int(value)-1)
