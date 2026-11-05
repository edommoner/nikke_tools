"""Exact static post-fire delays; no CPU battle, timers or computed shot times."""
import math,struct
MAGIC=0x57464331
WORDS=16

def compile_clock(weapons,delays):
 if len(weapons)!=5 or not isinstance(delays,list) or len(delays)!=5:raise ValueError('Five exact post-fire delays required')
 words=[MAGIC,1,5,0]
 for weapon,value in zip(weapons,delays):
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=180 or weapon.get('mode')!='charge' and value!=0:raise ValueError('Invalid exact post-fire delay')
  words.extend(struct.unpack('<II',struct.pack('<d',value)))
 return words+[0,0]

def normalize_static_clock(chars,attacks,enemy):
 from calculator.timeline import CharState
 if len(chars)!=5 or len(attacks)!=5:raise ValueError('Five static weapon definitions required')
 return [state.post_fire_delay if state.fire_mode=='charge' else 0.0 for state in (CharState(char,attack,enemy.get('code')) for char,attack in zip(chars,attacks))]
