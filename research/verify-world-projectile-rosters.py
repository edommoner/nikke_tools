"""Eleven newly packable real profiles; complete effects, two battle durations."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker
from detail_coverage import body_for
from portable_backend import execute,source_hashes
from portable_runtime import decode
from portable_projectile_roster_input import compile_projectile_battle,SOURCE,INPUT_WORDS,OUTPUT_WORDS
from portable_projectile_specs import HEAD,TRACE,TRACE_COUNT
from world_projectile_native import capture_projectile_shots
from world_real_binding_proof import binding_view
s=importlib.util.spec_from_file_location('projectile_roster_oracle',ROOT/'scripts/verify-portable-real-battle.py');reference=importlib.util.module_from_spec(s);s.loader.exec_module(reference)
s=importlib.util.spec_from_file_location('projectile_roster_policy',ROOT/'research/audit-world-roster-input.py');policy=importlib.util.module_from_spec(s);s.loader.exec_module(policy)
PROFILES=[('네온 : 비전 아이',0),('베스티',0),('라플라스',0),('라플라스',1),('라플라스',2),('라플라스',3),('도로시 : 세렌디피티',0),('레오나',0),('아르카나 : 포츈 메이트',0),('파워',0),('A2',0)]

def prepare():
 rows=[]
 for name,stage in PROFILES:
  for duration in (3,30):
   b=dict(body_for(policy.roster_for(name),duration),burst_gauge_mode='accumulate');b['profile']['chars'][name]['favorite_stage']=stage
   if stage:b['profile']['chars'][name]['collection_stage']='SR15'
   p=engine_worker.evaluate(dict(b,_portable_static_inputs=True));w,m=compile_projectile_battle(p);rows.append((dict(character=name,favorite_stage=stage,duration=duration,body=b),p,w,m))
 return rows

def native_reference(body):
 with capture_projectile_shots(body['squad']) as shots:r=reference.native_reference(body)
 return r,shots

def trace(block):
 assert block[HEAD]==0x57505231 and block[HEAD+1]<=TRACE_COUNT and block[HEAD+3]<=1 and not any(block[HEAD+4:HEAD+16]);rows=[]
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for i in range(block[HEAD+1]):
  at=TRACE+i*16;assert block[at]<5 and block[at+1]<3 and block[at+7]==0 and not any(block[at+10:at+16])
  rows.append(dict(owner=block[at],mode=block[at+1],time=number(at+2),pellets=block[at+4],muzzles=block[at+5],reach=block[at+6],damage=number(at+8)))
 return rows,block[HEAD+2]

def compare(block,prepared,program,native,shots):
 w,m=program;actual=decode(block[:159744],m);p,cpu=binding_view(prepared,native,m)
 diff=reference.compare_native_result(actual,p,cpu,program=program);events,omitted=trace(block)
 diff+=reference.differences(events,shots[:TRACE_COUNT],'physical_shots')
 if len(shots)-len(events)!=omitted:diff.append(dict(path='physical_history_omitted',gpu=omitted,cpu=len(shots)-len(events)))
 return actual,events,omitted,diff
