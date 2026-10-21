"""Canonical named coefficient/received-damage operators, outside numeric64."""
from effect_spec import NAMED_MAGNITUDE

STATS={name:NAMED_MAGNITUDE[name] for name in ('dmg_scale_mag_pct','received_dmg_buff_mag_pct')}


def validate(effect,*,combat,world_frame):
    if effect.get('stat') not in STATS:return
    if effect.get('type')!='buff' or combat is None or not world_frame:
        raise ValueError('Named magnitude requires a private combat world buff')
    if not isinstance(effect.get('target_effect'),str) or not effect['target_effect']:
        raise ValueError('Named magnitude requires a nonempty target_effect')
    if not ('fixed_value' in effect or 'values' in effect):
        raise ValueError('Named magnitude requires an authored quantity')
