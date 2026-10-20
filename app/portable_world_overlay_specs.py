"""Static authored overlay payload;world transitions are never CPU input."""
import math,struct
MAGIC=0x574f3031
NODE_WORDS=16
INPUT_WORDS=528

def number(value):
 if type(value) not in (int,float):raise ValueError('Overlay requires finite numeric input')
 try:valid=math.isfinite(value)
 except OverflowError:valid=False
 if not valid:raise ValueError('Overlay requires finite numeric input')
 return list(struct.unpack('<II',struct.pack('<d',float(value))))

def compile_payload(patterns):
 if not 1<=len(patterns)<=32:raise ValueError('World overlay node capacity exceeded')
 words=[MAGIC]+[0]*527
 for p in patterns:
  at=16+p.idx*16
  if p.kind in ('idle','groggy','attack'):continue
  if p.kind=='buff':
   value=p.enemy_effect['fixed_value'] if p.enemy_effect else 0
   words[at:at+10]=[1,int(p.irremovable),*number(p.def_mult),*number(p.def_add),*number(value),0,0]
  elif p.kind=='core':
   if p.core_px>100000000:raise ValueError('Overlay core diameter exceeds literal geometry bound')
   words[at]=2;words[at+8:at+10]=number(p.core_px)
  elif p.kind=='move':
   if p.distance is not None:words[at]=3;words[at+8:at+10]=number(p.distance)
   else:
    from portable_geometry_specs import WEAPONS
    words[at]=4;words[at+10]=sum(1<<(WEAPONS[w]-1) for w in p.weapons)
  else:raise ValueError('World overlay payload still needs landing/gauge/actor connection: '+p.kind)
 return words
