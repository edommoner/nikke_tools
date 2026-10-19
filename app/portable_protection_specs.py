"""Shared static protection metadata; amounts and absorption remain GPU-owned."""
KINDS={'shield_from_max_hp_pct':1,'shared_shield_from_max_hp_pct':1,'decoy':2,'next_shield_hp_pct':3,'shield_invincible':4,'shield_heal_pct':5,'decoy_heal_pct':6,'cover_disabled':7}

def policy(effect):
 stat=effect.get('stat');kind=KINDS.get(stat,0) if isinstance(stat,str) else 0
 if not kind:return 0
 if 'fixed_value' in effect:
  import math
  value=effect['fixed_value']
  try:finite=type(value) in (int,float) and math.isfinite(float(value))
  except (ValueError,OverflowError):finite=False
  if not finite:raise ValueError('Protection quantity must be finite numeric input')
 expected='instant' if kind in (5,6) else 'buff'
 if effect.get('type')!=expected:raise ValueError('Protection effect has the wrong kind')
 if 'end_on_shield_consumed' in effect and (kind!=1 or type(effect['end_on_shield_consumed']) is not bool):raise ValueError('Invalid shield consumption lifetime')
 if kind in (5,6) and effect.get('scaling') not in (None,'max_hp'):raise ValueError('Unported protection healing basis')
 return kind | (int(effect.get('end_on_shield_consumed',False))<<8)

def pack(words,index,effect,L):
 value=policy(effect);words[L['PROTECTION_DEFINITION_BASE']+index]=value
 if value:words[L['PROTECTION_META_BASE']]|=1
