"""Cast-time hit-count plans for attacks landing at full-burst entry.

This validates authored scheduling, not a character's real animation timing.
Coefficient/buff sampling belongs to landing; activation gates belong to cast.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class LandingPlan:
    count: int | str


def full_burst_landing(effect, burst_stage):
    if 'land_in_full_burst' not in effect:
        return None
    enabled = effect['land_in_full_burst']
    if type(enabled) is not bool:
        raise ValueError('Full-burst landing flag must be boolean')
    stat = effect.get('stat', '')
    root, separator, suffix = stat.partition(':') if isinstance(stat, str) else ('', '', '')
    direct = {'damage', 'burst_damage', 'split_damage', 'armor_break_damage',
              'armor_break_burst_damage', 'sequential_damage', 'projectile_attachment_damage',
              'projectile_explosion_damage', 'pierce_damage', 'core_damage'}
    if (effect.get('type') != 'damage' or root not in direct
            or effect.get('tick_interval') or 'burst_cast' not in effect.get('trigger', {}).get('timing', [])):
        raise ValueError('Full-burst landing requires a direct burst-cast attack')
    if not enabled or str(burst_stage) != '3':
        return None
    # The pinned reference currently latches the stat suffix only. Do not
    # silently discard another count source; extend both contracts first.
    if 'hit_count_gauge_ref' in effect or (effect.get('scaling') == 'stack_count' and not separator):
        raise ValueError('Full-burst landing count source must be an explicit stat suffix')
    if not separator:
        return LandingPlan(1)
    if not suffix:
        raise ValueError('Full-burst landing has an empty count reference')
    if suffix.lstrip('-').isdigit():
        count = int(suffix)
        if not -256 <= count <= 256:
            raise ValueError('Full-burst landing count exceeds instruction bounds')
        return LandingPlan(count)
    return LandingPlan(suffix)
