"""One native oracle and literal input suite for CUDA/Metal enemy spawn notifications."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import engine_worker
from world_skill_native import inspect as inspect_native
import world_spawn_cases as cases
s=importlib.util.spec_from_file_location('spawn_periodic','research/verify-world-periodic.py');periodic=importlib.util.module_from_spec(s);s.loader.exec_module(periodic)
s=importlib.util.spec_from_file_location('spawn_attack','research/verify-world-enemy-attack.py');attack=importlib.util.module_from_spec(s);s.loader.exec_module(attack)
physical=attack.physical

SOURCE='gpu/world_spawn_entry.slang';OUTPUT=L['WORLD_PERIODIC_OUTPUT_WORDS']
def fixtures():return cases.fixtures()
def compile_case(case):
 w,m,b=physical.pack.compile_case(case,allow_no_counter=True);w[0]=L['WORLD_SPAWN_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=15
 from portable_enemy_specs import damage_plan
 for i,e in enumerate(case['effects']):
  if e.get('type')=='damage' and damage_plan(e)[0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b
def decoded(block,meta,case,bindings):
 r=attack.decoded(block,meta,case,bindings);r['periodic_runtime']=periodic.decoded(block,meta,case,bindings)['periodic_runtime'];head=L['WORLD_SPAWN_HEAD_BASE'];count=block[head+1];assert block[head]==0x57534e31 and block[head+2]==1 and count<=4096 and not any(block[head+3:head+8]);notes=[]
 for i in range(count):
  at=L['WORLD_SPAWN_TRACE_BASE']+i*4;assert block[at]<5 and block[at+3]==0;notes.append(dict(owner=block[at],time=struct.unpack('<d',struct.pack('<II',*block[at+1:at+3]))[0]))
 r['enemy_spawn_notifications']=notes;return r
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[0][0];bad=[]
 for name,at,value in [('spawn-old-mode13',L['TARGET_COUNTER_INPUT_BASE']+6,13),('spawn-unknown-mode16',L['TARGET_COUNTER_INPUT_BASE']+6,16),('spawn-without-landings',L['LANDING_META_BASE'],0),('spawn-invalid-owner',L['DEFINITION_BASE']+F['OWNER'],5),('spawn-missing-candidate-mask',L['EVENT_CANDIDATE_BASE']+5*L['MASK_WORDS'],0)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad
def sha(b):return hashlib.sha256(b).hexdigest()
