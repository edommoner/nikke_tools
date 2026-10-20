"""Literal direct-boss attack payload shared by all common-world entry packers."""
from portable_world_schedule_specs import number
from portable_enemy_target_specs import target_rule

def pack_attacks(words,patterns,authored,L):
 for p in patterns:
  if p.attack is None:continue
  raw=authored[p.idx]['spec'];at=L['WORLD_FRAME_PAYLOAD_BASE']+p.idx*16
  if raw.get('debuffs'):raise ValueError('Attack debuff payload is not connected')
  words[at:at+16]=[32,0,0,int(p.attack.pierce),0,0,0,0,*number(p.attack.atk or 114344),*number(p.attack.coeff),*target_rule({k:raw[k] for k in ('target','ignore_taunt') if k in raw})]
