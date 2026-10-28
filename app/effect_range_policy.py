"""Explicit named radial growth using existing carrier/query rules.

The base radius and colliders are declared model inputs, not game distances.
This reader does not install a canonical consumer or mutate a live manager.
"""
import math
from effect_target_count_policy import _Query
STAT='effect_range_pct'
MODEL='named-effect-radial-growth-v1'

def validate_effect(effect):
    if effect.get('stat')!=STAT:return False
    target=effect.get('target');value=effect.get('fixed_value')
    if (effect.get('type')!='buff' or not (target in ('self','all_allies') or isinstance(target,str) and target.startswith('allies_with_buff:') and target.split(':',1)[1])
        or type(effect.get('target_effect')) is not str or not effect['target_effect']
        or type(value) not in (int,float) or not math.isfinite(value) or value < -100
        or any(effect.get(k) is not None for k in ('scaling','scaling_ref','values','tick_interval','tick_start'))):
        raise ValueError('Named range requires fixed finite allied modifiers and an exact effect name')
    return True

def query(manager,caster,marker,when,*,base_radius,model):
    from calculator.buff_manager import BuffManager
    if (model!=MODEL or not isinstance(manager,BuffManager) or caster not in manager.squad_names
        or type(marker) is not str or not marker or type(when) not in (int,float) or not math.isfinite(when) or when<0
        or type(base_radius) not in (int,float) or not math.isfinite(base_radius) or base_radius<0):
        raise ValueError('Explicit finite named radial context required')
    for effect,_ in manager._effects:validate_effect(effect)
    for ab in manager._active:
        if validate_effect(ab.effect) and ab.target_chars is None:raise ValueError('Lazy range recipients require a separate lifecycle contract')
    total=_Query(manager,marker,STAT).get_buffs(caster,'__enemy__',when)[STAT]
    factor=1.+total/100.;radius=base_radius*factor
    if not all(math.isfinite(v) and v>=0 for v in (factor,radius)):raise ValueError('Named range result outside finite nonnegative domain')
    return dict(percent=total,factor=factor,base_radius=float(base_radius),radius=radius)
