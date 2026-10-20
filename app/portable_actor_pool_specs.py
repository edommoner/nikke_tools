"""Authored Actor pool quantities;no HP,death schedule or recipients are simulated."""
import math,struct
from portable_specs import LIMITS as L
MAGIC=0x57485031
REF=0x80000000

def number(v):
 if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('Finite Actor quantity required')
 return list(struct.unpack('<II',struct.pack('<d',float(v))))

def compile_pools(patterns,bindings):
 from calculator.boss_pattern import BOSS_EVENTS
 words=[0]*(L['WORLD_ACTOR_POOL_INPUT_WORDS']-L['WORLD_ACTOR_INPUT_WORDS']);words[:2]=[MAGIC,len(bindings)]
 for slot,b in enumerate(bindings):
  if slot==0:continue
  p=patterns[b.run];at=8+slot*12
  if int(b.kind)==1:
   spec=p.targets[b.slot]
   if len(spec.emits)>8:raise ValueError('Actor death notice capacity exceeded')
   if spec.score>0x7fffffff:raise ValueError('Actor score exceeds exact integer bound')
   words[at:at+12]=[1,0,*number(spec.hp),0,0,len(spec.emits),sum((BOSS_EVENTS.index(e)+1)<<(i*3) for i,e in enumerate(spec.emits)),spec.score,0,0,0]
  else:
   spec=p.summon;mode=4 if spec.hp is not None and spec.hit_hp else 3 if spec.hp is None else 2
   if not 0<=spec.hit_hp<=0x7fffffff:raise ValueError('Actor hit-HP exceeds exact integer bound')
   words[at:at+12]=[mode,spec.hit_hp,*number(spec.hp or 0),*number(spec.hit_hp_after),0,0,0,0,0,0]
 return words
