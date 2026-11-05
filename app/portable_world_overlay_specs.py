"""Static authored overlay payload;world transitions are never CPU input."""
import math,struct
MAGIC=0x574f3031
NODE_WORDS=16
INPUT_WORDS=528
CODES={name:i+1 for i,name in enumerate(('작열','수냉','풍압','철갑','전격'))}

def number(value):
 if type(value) not in (int,float):raise ValueError('Overlay requires finite numeric input')
 try:valid=math.isfinite(value)
 except OverflowError:valid=False
 if not valid:raise ValueError('Overlay requires finite numeric input')
 return list(struct.unpack('<II',struct.pack('<d',float(value))))

def compile_payload(patterns,*,camera_mask=0,element_codes=(),code_tags=None,charge_hold_mask=0,actor_pools=False,named_refs=None):
 if not 1<=len(patterns)<=32:raise ValueError('World overlay node capacity exceeded')
 if type(camera_mask) is not int or not 0<=camera_mask<=31:raise ValueError('Invalid static camera mask')
 if element_codes and (len(element_codes)!=5 or any(x not in range(6) for x in element_codes)):raise ValueError('Invalid roster element codes')
 if type(charge_hold_mask) is not int or not 0<=charge_hold_mask<=31:raise ValueError('Invalid charge hold owner mask')
 words=[MAGIC]+[0]*527;words[1]=camera_mask;words[7]=0x48410000|charge_hold_mask if charge_hold_mask else 0
 if element_codes:words[2:7]=element_codes
 code_tags=code_tags or {}
 named_refs=named_refs or {}
 for p in patterns:
  at=16+p.idx*16
  if p.kind in ('idle','groggy','attack','debuff') or actor_pools and p.kind in ('parts','interrupt','summon'):continue
  if p.kind=='buff':
   value=p.enemy_effect['fixed_value'] if p.enemy_effect else 0
   words[at:at+10]=[1,int(p.irremovable),*number(p.def_mult),*number(p.def_add),*number(value),0,0]
   if p.enemy_effect and p.enemy_effect.get('name') in named_refs:
    name=named_refs[p.enemy_effect['name']]
    if type(name) is not int or not 1<=name<=256:raise ValueError('Invalid named overlay reference')
    words[at+11]=name
  elif p.kind=='core':
   if p.core_px>100000000:raise ValueError('Overlay core diameter exceeds literal geometry bound')
   words[at]=2;words[at+8:at+10]=number(p.core_px)
  elif p.kind=='move':
   if p.distance is not None:words[at]=3;words[at+8:at+10]=number(p.distance)
   else:
    from portable_geometry_specs import WEAPONS
    words[at]=4;words[at+10]=sum(1<<(WEAPONS[w]-1) for w in p.weapons)
  elif p.kind=='shield':
   words[at]=5;words[at+8]=code_tags.get(p.code,0);words[at+10]=CODES[p.code]
  elif p.kind=='vanish':words[at]=6
  else:raise ValueError('World overlay payload still needs actor connection: '+p.kind)
 return words

def compiler_effect(effect):
 """Use the existing typed instant selector;the overlay flag owns semantics."""
 if effect.get('type')=='weapon_change' and 'skill_damage' in effect:
  if type(effect['skill_damage']) is not bool:raise ValueError('Weapon mode skill policy requires boolean')
  result=dict(effect);result.pop('skill_damage');return result
 if effect.get('stat')!='enemy_buff_cleanse':return effect
 if effect.get('type')!='instant':raise ValueError('Enemy beneficial cleanse requires instant type')
 return dict(effect,stat='debuff_cleanse')

def pack_cleanse_flags(words,effects,limits):
 header=limits['WORLD_OVERLAY_INPUT_BASE']
 for row,effect in enumerate(effects):
  if effect.get('stat')!='enemy_buff_cleanse':continue
  compiler_effect(effect)
  at=limits['DEFINITION_BASE']+row*limits['DEFINITION_WORDS']
  if words[at+1]!=26:raise ValueError('Unexpected compiled cleanse kind')
  words[header+8+row//32]|=1<<(row%32)

def pack_skill_mode_flags(words,effects,limits):
 for row,effect in enumerate(effects):
  if effect.get('type')!='weapon_change' or not effect.get('skill_damage'):continue
  compiler_effect(effect)
  if words[limits['DEFINITION_BASE']+row*limits['DEFINITION_WORDS']+1]!=2:raise ValueError('Unexpected compiled weapon mode kind')
  words[limits['MODE_BASE']+row*limits['MODE_WORDS']+31]=1
