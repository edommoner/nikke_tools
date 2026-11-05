"""Canonical authored policy into isolated full executor; native closures after readback."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts'),str(R/'research')]
import portable_runtime as runtime,portable_enemy_specs as enemy_specs
from portable_specs import LIMITS as L
from portable_enemy_target_specs import ABI,pack,META_BASE,RNG_BASE,QUERY_BASE
from enemy_target_native import observe

def core_module():
 s=importlib.util.spec_from_file_location('enemy_target_common',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v

def compile_case(c,v):
 # Temporary host admission only; the final wire contains rules,never selected masks.
 temporary=copy.deepcopy(c);temporary.pop('enemy_targeting',None)
 for cmd in temporary['script']:
  if cmd[1]==32:cmd[1]=31;cmd[4]=31
 buffs,enemies=runtime.BUFFS,enemy_specs.ENEMY_BUFF_STATS
 try:
  runtime.BUFFS=buffs|{'taunt','stealth'};enemy_specs.ENEMY_BUFF_STATS=enemies|{'taunt'}
  words,metadata=v.compile_case(temporary)
 finally:runtime.BUFFS=buffs;enemy_specs.ENEMY_BUFF_STATS=enemies
 words[0]=ABI
 for step,cmd in enumerate(c['script']):
  if cmd[1]==32:
   assert cmd[3]==0 and cmd[4]==0 and cmd[5]==-1
   at=L['COMMAND_BASE']+step*8;words[at]=32;words[at+4]=0;words[at+5]=0
 metadata['enemy_targeting']=pack(words,c.get('enemy_targeting'),c['script'],list(zip(c['effects'],c.get('owners',[0]*len(c['effects'])))))
 return words,metadata
