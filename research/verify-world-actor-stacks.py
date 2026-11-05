"""Typed128 stack controls use the existing numeric and deferred notice loop."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_stack_specs import plan
import world_actor_stack_cases as cases
s=importlib.util.spec_from_file_location('typed_stack_status',ROOT/'research/verify-world-actor-status.py');status=importlib.util.module_from_spec(s);s.loader.exec_module(status)
SOURCE='gpu/world_actor_stack_entry.slang';MAGIC=0x57543031

def fixtures():return cases.fixtures(status)
def compile_case(c):
 w,m,b=status.compile_case(c);w[0]=L['WORLD_ACTOR_STACK_ABI'];w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC
 for i,e in enumerate(c['effects']):
  p=plan(e,combat=c['combat'])
  if p is not None and p[1]==2 and p[2][0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b

decoded=status.decoded

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0]
 for name,at,value in [('unknown-stack-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57543032),('stack-control-disabled-in-status-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57493031),('stack-nonfinite-delta',L['DEFINITION_BASE']+32+7,0x7ff00000),('stack-route-overflow',L['DAMAGE_DEFINITION_BASE']+8,10),('stack-scope-count-zero',L['DAMAGE_DEFINITION_BASE']+9,0),('stack-scope-count-overflow',L['DAMAGE_DEFINITION_BASE']+9,257),('stack-packet-reserved',L['DAMAGE_DEFINITION_BASE']+10,1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 import copy
 edge=copy.deepcopy(next(c for c in rows if c['name']=='unlimited-last-exact31bit-stack'));edge['effects'][1]['fixed_value']=2147483647;ew,_,_=compile_case(edge);bad.append(('unlimited-stack-exceeds31bit-storage',ew))
 return rows,programs,bad
