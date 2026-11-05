"""One native oracle and literal input suite for CUDA/Metal critical/core notifications."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import engine_worker
from world_skill_native import inspect as inspect_native
import world_fraction_cases as cases
s=importlib.util.spec_from_file_location('fraction_spawn','research/verify-world-spawn.py');spawn=importlib.util.module_from_spec(s);s.loader.exec_module(spawn)
physical=spawn.physical;periodic=spawn.periodic

INPUT=L['WORLD_FRACTION_INPUT_WORDS'];SOURCE='gpu/world_fraction_entry.slang';OUTPUT=L['WORLD_PERIODIC_OUTPUT_WORDS']
def fixtures():return cases.fixtures()
def compile_case(case):
 w,m,b=physical.pack.compile_case(case,allow_no_counter=True);w[0]=L['WORLD_FRACTION_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=17
 from portable_enemy_specs import damage_plan
 for i,e in enumerate(case['effects']):
  if e.get('type')=='damage' and damage_plan(e)[0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 from portable_charge_clock_specs import compile_clock
 w.extend(compile_clock(case['combat']['weapons'],case['post_fire_delays']));assert len(w)==INPUT
 return w,m,b
def decoded(block,meta,case,bindings):
 r=spawn.decoded(block,meta,case,bindings);head=L['WORLD_FRACTION_HEAD_BASE'];count=block[head+1];mask=block[head+2];rows=meta.get('_original_fraction_rows');assert block[head]==0x57465231 and (count<=2048 if rows is None else len(rows)==count) and mask<1024 and not any(block[head+3:head+8]);notes=[]
 if rows is not None and any(block[L['WORLD_FRACTION_TRACE_BASE']:L['WORLD_FRACTION_TRACE_BASE']+2048*8]):raise AssertionError('Relocated fraction trace must leave its old bank empty')
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for i in range(count):
  at=L['WORLD_FRACTION_TRACE_BASE']+i*8;row=list(block[at:at+8]) if rows is None else rows[i];packed=row[1];assert len(row)==8 and row[0] in (22,23) and packed&7<5 and packed<32
  value=lambda pos:struct.unpack('<d',struct.pack('<II',*row[pos:pos+2]))[0]
  notes.append(dict(event=row[0],owner=packed&7,time=value(2),fraction=value(4),fired=(packed>>3)&1,created=bool(packed&16),after=value(6)))
 r['fractional_hits']=notes;r['fractional_accumulators']=[dict(event=22+kind,owner=who,value=number(L['WORLD_FRACTION_STATE_BASE']+who*8+kind*2)) for who in range(5) for kind in (1,0) if mask&(1<<(who*2+kind))];return r
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[0][0];bad=[]
 for name,at,value in [('fraction-old-mode15',L['TARGET_COUNTER_INPUT_BASE']+6,15),('fraction-unknown-mode18',L['TARGET_COUNTER_INPUT_BASE']+6,18),('fraction-without-landings',L['LANDING_META_BASE'],0),('fraction-invalid-owner',L['DEFINITION_BASE']+F['OWNER'],5),('fraction-missing-candidate-mask',L['EVENT_CANDIDATE_BASE']+22*L['MASK_WORDS'],0)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 clock=L['WORLD_FRACTION_CLOCK_BASE']
 for name,at,value in [('clock-magic',clock,0),('clock-version',clock+1,2),('clock-reserved',clock+15,1),('clock-nan',clock+5,0x7ff80000),('clock-negative',clock+5,0xbff00000),('clock-noncharge-delay',clock+5,0x3ff00000)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad
def sha(b):return hashlib.sha256(b).hexdigest()
