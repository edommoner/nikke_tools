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
 r=spawn.decoded(block,meta,case,bindings);head=L['WORLD_FRACTION_HEAD_BASE'];count=block[head+1];mask=block[head+2];assert block[head]==0x57465231 and count<=2048 and mask<1024 and not any(block[head+3:head+8]);notes=[]
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for i in range(count):
  at=L['WORLD_FRACTION_TRACE_BASE']+i*8;packed=block[at+1];assert block[at] in (22,23) and packed&7<5 and packed<32;notes.append(dict(event=block[at],owner=packed&7,time=number(at+2),fraction=number(at+4),fired=(packed>>3)&1,created=bool(packed&16),after=number(at+6)))
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
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args()
 rows,programs,bad=prepare();observed=[inspect_native(c) for c in rows];native=[n for n,t in observed]
 if a.cpu_only:print('Critical/core native',len(rows),'raw',len(bad),'GPU0');return
 packed=array.array('I',[len(rows)+len(bad)])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();ow=OUTPUT*4
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();e=json.loads((folder/'evidence.json').read_text());assert e['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-fraction-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(SOURCE,'portableEvents',data,INPUT,OUTPUT,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 checked=[]
 for i,(c,(_,m,b),n) in enumerate(zip(rows,programs,native)):
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  try:
   r=decoded(block,m,c,b);changed=[k for k in n if k!='scope' and r[k]!=n[k]];trace=periodic.skill_trace(block)
   if trace!=observed[i][1]:changed.append('skill_trace')
  except Exception as error:r=dict(error=repr(error));changed=['decode'];trace=[]
  checked.append(dict(name=c['name'],passed=block[0]==0 and not changed,status=block[0],changed=changed,actual=r,native=n,skill_trace=trace,native_skill_trace=observed[i][1]))
 rejected=[dict(name=name,status=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little'),passed=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little')==64) for i,(name,_) in enumerate(bad)]
 report=dict(passed=all(c['passed'] for c in checked+rejected),cases=checked,rejected_cases=rejected,captured=str(folder),evidence=e,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),unchanged_gpu_retries=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-fraction-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[(c['name'],c.get('changed'),c['status']) for c in checked+rejected if not c['passed']];print('Critical/core',len(rows),'native',len(bad),'raw',a.backend)
if __name__=='__main__':main()
