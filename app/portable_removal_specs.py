"""Named removal scope; recipient state and timer retirement stay GPU owned."""
from portable_recipient_specs import admitted
from portable_enemy_specs import enemy_buff_plan

def plan(effect, *, combat=None):
    if 'remove_scope' in effect and (effect.get('type')!='instant' or effect.get('stat')!='remove_named_buff'):
        raise ValueError('Removal scope requires named removal')
    if effect.get('type')!='instant' or effect.get('stat')!='remove_named_buff':return None
    if not isinstance(effect.get('target_effect'),str):raise ValueError('Named removal requires a state name')
    scope=effect.get('remove_scope','global')
    if scope not in ('global','target'):raise ValueError('Unknown named removal scope')
    target=effect.get('target','self')
    if not isinstance(target,str):raise ValueError('Named removal target must be a string')
    if scope=='global':return 0,None
    if admitted(target,instant=True):return 1,None
    from calculator.buff_manager import _NIKKE
    if target in _NIKKE:return 1,None
    enemy=enemy_buff_plan(dict(type='buff',stat='def_pct',target=target))
    if enemy is not None:
        if combat is None:raise ValueError('Enemy removal requires combat-owned targets')
        return 2,enemy
    raise ValueError('Unported named removal recipient selector')
