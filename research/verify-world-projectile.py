"""Shared CUDA/Metal physical projectile numbers versus full native simulation."""
import argparse,array,datetime,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from portable_projectile_specs import ABI,MODE,HEAD,TRACE,TRACE_COUNT,finalize_program
from world_projectile_cases import fixtures
from world_projectile_native import observe as inspect_native
s=importlib.util.spec_from_file_location('projectile_reload','research/verify-world-reload.py');reload=importlib.util.module_from_spec(s);s.loader.exec_module(reload)
SOURCE='gpu/world_projectile_entry.slang';INPUT=104400;OUTPUT=786432

def compile_case(c):
 w,m,b=reload.compile_case(c);finalize_program(w);return w,m,b

def decoded(block,meta,case,bindings):
 r=reload.decoded(block,meta,case,bindings);head=HEAD;assert block[head]==0x57505231 and block[head+1]<=TRACE_COUNT and block[head+2]==0 and block[head+3]<=1 and not any(block[head+4:head+16]);events=[]
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for i in range(block[head+1]):
  at=TRACE+i*16;assert block[at]<5 and block[at+1]<3 and block[at+7]==0 and not any(block[at+10:at+16])
  events.append(dict(owner=block[at],mode=block[at+1],time=number(at+2),pellets=block[at+4],muzzles=block[at+5],reach=block[at+6],damage=number(at+8)))
 r['projectile_shots']=events
 if case.get('observe_pending_skills'):
  from world_pending_state import pending_state
  r['pending_burst']=pending_state(block)
 return r

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[0][0];bad=[]
 for name,at,value in [('old-roster-abi',0,0x5045568c),('old-roster-mode',L['TARGET_COUNTER_INPUT_BASE']+6,23),('projectile-kind',L['DEFINITION_BASE']+F['KIND'],4),('projectile-nan',L['DEFINITION_BASE']+F['VALUE']+1,0x7ff80000),('projectile-no-combat',3,0)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 for name,value in [('pellet-cap-overflow',4097),('positive-huge-pellet-count',1e200)]:
  w=list(seed);pos=L['DEFINITION_BASE']+F['VALUE'];w[pos:pos+2]=list(struct.unpack('<II',struct.pack('<d',value)));bad.append((name,w))
 for name,kind,key,arg in [('resource-key-overflow',18,256,0),('resource-mod-zero',21,0,0),('resource-mod-fractional',21,0,2.5)]:
  w=list(seed);w[L['RESOURCE_META_BASE']]=1;w[L['DEFINITION_BASE']+F['CONDITION_COUNT']]=1;at=L['CONDITION_BASE'];w[at:at+4]=[kind,key,*struct.unpack('<II',struct.pack('<d',arg))];bad.append((name,w))
 w=list(programs[-1][0]);w[L['RECIPIENT_BASE']+2*8+6]=1;bad.append(('self-removal-unused-recipient-key',w))
 return rows,programs,bad
