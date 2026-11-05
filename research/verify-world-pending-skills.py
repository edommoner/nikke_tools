"""Common pending batch oracle and saved-word regression for CUDA and Metal."""
import argparse,array,datetime,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import world_pending_cases as cases
physical=cases.suite.physical;skill_trace=cases.suite.skill_trace;inspect_native=cases.suite.inspect_native
SOURCE='gpu/world_pending_entry.slang'
def fixtures():return cases.fixtures()
def compile_case(case):return cases.compile_case(case)
def decoded(block,meta,case,bindings):
 r=physical.decoded(block,meta,case,bindings);from world_pending_state import pending_state;r['pending_burst']=pending_state(block);return r
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[0][0];bad=[];row=1;packet=L['DAMAGE_DEFINITION_BASE']+row*8;definition=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
 for name,at,value in [('pending-unknown-mode8',L['TARGET_COUNTER_INPUT_BASE']+6,8),('pending-unknown-mode10',L['TARGET_COUNTER_INPUT_BASE']+6,10),('pending-in-old-direct-mode',L['TARGET_COUNTER_INPUT_BASE']+6,7),('pending-zero-hits',packet+7,0),('pending-hits-overflow',packet+7,257),('pending-invalid-flag',packet+6,2),('pending-nonplain-multihit',packet+2,2),('pending-unresolved-normal-formula',packet+3,1),('pending-unresolved-formula-flag',definition+F['DAMAGE_FLAGS'],256),('pending-dot-unported',definition+F['DAMAGE_FLAGS'],128),('pending-without-cast-trigger',L['EVENT_BASE']+row*L['EVENT_WORDS'],0)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad
