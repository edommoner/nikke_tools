"""Full native shared recipient contracts;one executable for CUDA and Metal."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_removal_specs import plan
from portable_enemy_specs import enemy_buff_plan
import world_actor_recipient_cases as cases
s=importlib.util.spec_from_file_location('recipient_state',ROOT/'research/verify-world-actor-state.py');state=importlib.util.module_from_spec(s);s.loader.exec_module(state)
SOURCE='gpu/world_actor_recipient_entry.slang';MAGIC=0x57523031

def fixtures():return cases.fixtures(state)
def compile_case(c):
 w,m,b=state.compile_case(c);w[0]=L['WORLD_ACTOR_RECIPIENT_ABI'];w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC
 for i,e in enumerate(c['effects']):
  p=plan(e,combat=c['combat'])
  if p is not None and p[0]==2 and p[1][0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b

def decoded(block,meta,c,bindings):
 old=array.array('I',block[:262144]);rows=[];members=[]
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for j in range(block[9]):
  p=L['CARRIER_STATE_BASE']+j*L['CARRIER_WORDS'];slot,definition=block[p:p+2];key=L['WORLD_ACTOR_FIELD_KEY_BASE']+slot*4
  if block[key]&0x80000000:old[key:key+4]=array.array('I',[0]*4)
  if not block[p+4]&1:continue
  at=L['WORLD_ACTOR_RECIPIENT_BASE']+16+slot*L['WORLD_ACTOR_RECIPIENT_WORDS'];kind,count=block[at:at+2]
  if kind==0 or enemy_buff_plan(c['effects'][definition]) is None:continue
  handles=[];live=[]
  for i in range(count):
   target=(block[at+136+i//4]>>((i%4)*8))&255;b=bindings[target];h=[int(b.kind),b.identity,block[at+8+target]];handles.append(h)
   if block[at+2+target//32]&(1<<(target%32)):live.append(h)
  row=dict(name=c['effects'][definition]['name'],owner=c['owners'][definition],stack=block[p+3],activated=number(p+7),end=number(p+5))
  if len(handles)==1:row['actor']=handles[0]
  else:row['actors']=handles
  rows.append(row);members.append(live)
 actual=state.decoded(old,meta,c,bindings);actual['enemy_fields']['carriers']=rows;actual['enemy_fields']['recipient_memberships']=members;return actual

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0]
 for name,at,value in [('unknown-recipient-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57523032),('shared-init-disabled-in-mutation-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x574D3031),('init-definition-index-overflow',L['MODE_BASE']+32+4,257),('init-nonfinite-value',L['DEFINITION_BASE']+32+7,0x7ff00000)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad
