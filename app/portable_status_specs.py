"""Shared static status admission; application, charge pools and removal stay GPU owned."""
import math
from portable_recipient_specs import admitted

def immunity(effect):
 if effect.get('type')!='buff':return 0
 stat=effect.get('stat')
 return 1 if stat=='debuff_immune' else 2 if isinstance(stat,str) and stat.startswith('debuff_immune:') else 3 if stat=='debuff_immune_count' else 0

def cleanse_plan(effect,*,combat=None):
 if effect.get('stat')!='debuff_cleanse':return None
 if effect.get('type')!='instant':raise ValueError('Cleanse requires an instant effect')
 if 'fixed_value' in effect:
  raw=effect['fixed_value']
  try:valid=type(raw) in (int,float) and math.isfinite(float(raw))
  except (ValueError,OverflowError):valid=False
  if not valid:raise ValueError('Cleanse limit must be finite')
 target=effect.get('target','self')
 from calculator.buff_manager import _NIKKE
 if admitted(target,instant=True) or isinstance(target,str) and target in _NIKKE:return 1,None
 from portable_enemy_specs import enemy_buff_plan
 enemy=enemy_buff_plan(dict(type='buff',stat='def_pct',target=target))
 if enemy is not None:
  if combat is None:raise ValueError('Enemy cleanse requires combat-owned targets')
  return 2,enemy
 raise ValueError('Unported cleanse recipient selector')

def enabled(effects):return any(immunity(e) for e,_ in effects)
