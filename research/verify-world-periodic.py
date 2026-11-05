"""Shared periodic oracle; immutable wide packets and legacy prefix regression."""
import argparse,array,datetime,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import world_periodic_cases as cases
physical=cases.suite.physical;skill_trace=cases.suite.skill_trace;inspect_native=cases.suite.inspect_native
SOURCE='gpu/world_periodic_entry.slang';OUTPUT=L['WORLD_PERIODIC_OUTPUT_WORDS']
def fixtures():return cases.fixtures()
def compile_case(case):return cases.compile_case(case)
def snapshot(block,at):
 n=block[at];assert n<=128;slots=[(block[at+6+i//4]>>((i%4)*8))&255 for i in range(n)]
 assert len(set(slots))==n and all(slot<128 for slot in slots)
 bits=[0]*4
 for slot in slots:bits[slot//32]|=1<<(slot%32)
 assert list(block[at+2:at+6])==bits and all(((block[at+6+i//4]>>((i%4)*8))&255)==0 for i in range(n,128))
 return slots
def captured_members(block,at):
 stamp=block[at+1];out=[]
 for slot in snapshot(block,at):
  p=L['WORLD_ACTOR_POOL_STATE_BASE']+slot*16
  if slot==0 or block[p+10]<=stamp:out.append(slot)
 return out
def decoded(block,meta,case,bindings):
 r=physical.decoded(block,meta,case,bindings);timers=[];carriers=[]
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for row,e in enumerate(case['effects']):
  if e.get('type')!='damage' or not e.get('tick_interval'):continue
  at=L['STATE_BASE']+row*10
  if block[at+6]:timers.append((block[at+5],dict(row=row,due=number(at),expiry=number(at+2))))
 timers=[row for _,row in sorted(timers,key=lambda x:x[0])]
 for i in range(block[9]):
  at=L['CARRIER_STATE_BASE']+i*L['CARRIER_WORDS'];row=block[at+1];e=case['effects'][row]
  if not block[at+4]&1 or e.get('type')!='damage' or not e.get('tick_interval'):continue
  carriers.append(dict(row=row,stack=block[at+3],activated=number(at+7),end=number(at+5),recipients=captured_members(block,L['WORLD_PERIODIC_DEFINITION_BASE']+row*38)))
 r['periodic_runtime']=dict(timers=timers,carriers=carriers);return r
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[0][0];bad=[];p=L['DAMAGE_DEFINITION_BASE'];d=L['DEFINITION_BASE']
 for name,at,value in [('periodic-unknown-mode12',L['TARGET_COUNTER_INPUT_BASE']+6,12),('periodic-in-old-mode9',L['TARGET_COUNTER_INPUT_BASE']+6,9),('periodic-without-retention',L['PERIODIC_DEFINITION_BASE'],4),('periodic-flags-overflow',L['PERIODIC_DEFINITION_BASE'],8),('periodic-recipient-overflow',p+1,129),('periodic-hits-overflow',p+2,257),('periodic-pending-forgery',p+6,1),('periodic-interval-nan',d+F['INTERVAL']+1,0x7ff80000),('periodic-interval-infinity',d+F['INTERVAL']+1,0x7ff00000),('periodic-negative-interval',d+F['INTERVAL']+1,0xbfb99999),('dot-without-clock',d+F['INTERVAL'],0),('periodic-parts-unported',d+F['DAMAGE_FLAGS'],128|65536),('periodic-without-landings',L['LANDING_META_BASE'],0)]:
  w=list(seed);w[at]=value
  if name=='periodic-interval-infinity':w[d+F['INTERVAL']]=0
  if name=='dot-without-clock':w[d+F['INTERVAL']+1]=0
  bad.append((name,w))
 return rows,programs,bad
def sha(b):return hashlib.sha256(b).hexdigest()
