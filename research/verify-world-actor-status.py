"""Typed128 immunity and cleanse use the existing common status loop."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_status_specs import cleanse_plan
import world_actor_status_cases as cases
s=importlib.util.spec_from_file_location('wide_status_recipients',ROOT/'research/verify-world-actor-recipients.py');recipient=importlib.util.module_from_spec(s);s.loader.exec_module(recipient)
SOURCE='gpu/world_actor_status_entry.slang';MAGIC=0x57493031

def fixtures():return cases.fixtures(recipient)
def compile_case(c):
 w,m,b=recipient.compile_case(c);w[0]=L['WORLD_ACTOR_STATUS_ABI'];w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC
 for i,e in enumerate(c['effects']):
  p=cleanse_plan(e,combat=c['combat'])
  if p is not None and p[0]==2 and p[1][0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b

def decoded(block,meta,c,bindings):
 actual=recipient.decoded(block,meta,c,bindings);used=[]
 for name,index in meta['states'].items():
  for who in range(5+len(bindings)):
   at=(L['IMMUNITY_USED_BASE']+(who*256+index)*2) if who<5 else (L['WORLD_ACTOR_WIDE_IMMUNITY_BASE']+((who-5)*256+index)*2)
   value=struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
   if value:
    actor=[-1,who] if who<5 else [int(bindings[who-5].kind),bindings[who-5].identity];used.append(dict(actor=actor,name=name,used=value))
 actual['enemy_fields']['nonzero_immunity_used']=sorted(used,key=lambda x:(x['actor'],x['name']));return actual

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0]
 for name,at,value in [('unknown-status-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57493032),('enemy-immunity-disabled-in-recipient-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57523031),('count-nonfinite-capacity',L['DEFINITION_BASE']+7,0x7ff00000)]:
  w=list(compile_case(next(c for c in rows if c['name']=='128-count-immunity-2'))[0] if name=='count-nonfinite-capacity' else seed);w[at]=value;bad.append((name,w))
 c=next(c for c in rows if c['name']=='typed-cleanse-scope-enemies_top_hp:2');cw,_,_=compile_case(c)
 for name,at,value in [('cleanse-route-overflow',L['DAMAGE_DEFINITION_BASE']+8,10),('cleanse-count-zero',L['DAMAGE_DEFINITION_BASE']+9,0),('cleanse-count-overflow',L['DAMAGE_DEFINITION_BASE']+9,257),('cleanse-packet-reserved',L['DAMAGE_DEFINITION_BASE']+10,1)]:
  w=list(cw);w[at]=value;bad.append((name,w))
 import copy
 hit=copy.deepcopy(c);hit['patterns'][0]['spec'].pop('hp',None);hit['patterns'][0]['spec']['hit_hp']=2;hw,_,_=compile_case(hit);bad.append(('pure-hit-hp-max-rank-unresolved-native-contract',hw))
 return rows,programs,bad
