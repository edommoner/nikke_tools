"""Typed named removal from the canonical resident executor versus native."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_removal_specs import plan
import world_actor_mutation_cases as cases
s=importlib.util.spec_from_file_location('mutation_state',ROOT/'research/verify-world-actor-state.py');state=importlib.util.module_from_spec(s);s.loader.exec_module(state)
SOURCE='gpu/world_actor_mutation_entry.slang';MAGIC=0x574D3031

def fixtures():return cases.fixtures(state)
def compile_case(c):
 w,m,b=state.compile_case(c);w[0]=L['WORLD_ACTOR_MUTATION_ABI'];w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC
 for i,e in enumerate(c['effects']):
  p=plan(e,combat=c['combat'])
  if p is not None and p[0]==2 and p[1][0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];row=1;d=L['DEFINITION_BASE']+row*32;packet=L['DAMAGE_DEFINITION_BASE']+row*8
 for name,at,value in [('unknown-mutation-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x574D3032),('removal-disabled-in-state-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57533031),('removal-scope-overflow',d+21,3),('enemy-route-overflow',packet,10),('enemy-count-zero',packet+1,0),('enemy-count-overflow',packet+1,257),('enemy-packet-reserved',packet+2,1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad
