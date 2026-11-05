"""Named duration policy and immutable definition membership, shared by both GPUs."""
from portable_recipient_specs import admitted
from portable_enemy_specs import enemy_buff_plan


def plan(effect, *, combat=None):
    if effect.get('type')!='instant' or effect.get('stat')!='named_buff_duration_extend':return None
    if not isinstance(effect.get('target_effect'),str):raise ValueError('Duration extension requires a state name')
    target=effect.get('target','self')
    if not isinstance(target,str):raise ValueError('Duration extension target must be a string')
    from calculator.buff_manager import _NIKKE
    if admitted(target,instant=True) or target in _NIKKE:return 1,None
    enemy=enemy_buff_plan(dict(type='buff',stat='def_pct',target=target))
    if enemy is not None:
        if combat is None:raise ValueError('Enemy duration extension requires combat-owned targets')
        return 2,enemy
    raise ValueError('Unported duration extension recipient selector')


def members(effect,effects):
    prefix=effect['target_effect']
    if not prefix:return []
    return [i for i,(other,_) in enumerate(effects)
            if other.get('name','')==prefix or other.get('name','').startswith(prefix+' ')]
