"""One native oracle and literal input suite for CUDA/Metal critical/core notifications."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import engine_worker
from world_skill_native import inspect as inspect_native
import world_team_cases as cases
s=importlib.util.spec_from_file_location('fraction_spawn','research/verify-world-spawn.py');spawn=importlib.util.module_from_spec(s);s.loader.exec_module(spawn)
physical=spawn.physical;periodic=spawn.periodic

INPUT=L['WORLD_TEAM_INPUT_WORDS'];SOURCE='gpu/world_team_entry.slang';OUTPUT=L['WORLD_PERIODIC_OUTPUT_WORDS']
def fixtures():return cases.fixtures()
from world_team_native import observe as inspect_native
from portable_team_hit_specs import bound_effects,compile_policy
from world_frame_native import roster_names,authored_metadata
import copy

def compile_case(case):
 from portable_target_counter_program import compiler_effects,patch_program
 from portable_target_counter_specs import pack_battle
 from portable_world_schedule_specs import compile_schedule
 from portable_charge_clock_specs import compile_clock
 from portable_enemy_specs import damage_plan
 c=copy.deepcopy(case);c['effects']=compiler_effects(case['effects']);w,m,b=physical.pack.stack.compile_case(c)
 names=roster_names(case);metadata=authored_metadata(case);chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=metadata[n]) for n in names]
 original=[(e,names[o]) for e,o in zip(case['effects'],case['owners'])]
 patch_program(w,m,chars,original);bound=bound_effects(original,m,names)
 _,patterns=compile_schedule(dict(patterns=case['patterns'],clock='accumulated',duration=case['duration']),notice_payload=True)
 w.extend(pack_battle([(e,names.index(owner)) for e,owner in bound],w[2],names,m['states'],b,patterns,allow_no_counter=True))
 w.extend(compile_clock(case['combat']['weapons'],case['post_fire_delays']));w.extend(compile_policy(m,case['enemy'].get('has_parts',False)))
 w[0]=L['WORLD_TEAM_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=19
 for i,(e,_) in enumerate(bound):
  if e.get('type')=='damage' and damage_plan(e)[0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 assert len(w)==INPUT
 return w,m,b

def expanded_case(case,meta):
 c=copy.deepcopy(case);c['effects']=[case['effects'][i] for i in meta['binding_source_indices']];c['owners']=meta['binding_owners'];return c

def decoded(block,meta,case,bindings):
 r=fraction.decoded(block,meta,expanded_case(case,meta),bindings)
 head=L['WORLD_TEAM_HEAD_BASE'];count=block[head+1];mask=block[head+4]
 assert block[head]==0x57544831 and count<=1024 and mask<1024 and not any(block[head+5:head+12])
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 notes=[]
 for i in range(count):
  at=L['WORLD_TEAM_TRACE_BASE']+i*8;packed=block[at+1];assert block[at] in (44,45) and packed&7<5 and packed<32
  notes.append(dict(event=block[at],owner=packed&7,time=number(at+2),fraction=number(at+4),fired=(packed>>3)&1,created=bool(packed&16),after=number(at+6)))
 r['team_hits']=notes;r['team_counts']=list(block[head+2:head+4]);r['team_accumulators']=[dict(event=44+kind,owner=who,value=number(L['WORLD_TEAM_STATE_BASE']+who*4+kind*2)) for who in range(5) for kind in (0,1) if mask&(1<<(who*2+kind))]
 return r

def skill_trace(block,meta):
 trace=periodic.skill_trace(block)
 for r in trace:r['row']=meta['binding_source_indices'][r['row']]
 return trace

s=importlib.util.spec_from_file_location('team_fraction_decode','research/verify-world-fraction.py');fraction=importlib.util.module_from_spec(s);s.loader.exec_module(fraction)
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[0][0];bad=[]
 for name,at,value in [
  ('team-counter-marker-zero',L['TARGET_COUNTER_INPUT_BASE'],0),('team-counter-marker-invalid',L['TARGET_COUNTER_INPUT_BASE'],1),('team-old-mode17',L['TARGET_COUNTER_INPUT_BASE']+6,17),
  ('team-unknown-mode20',L['TARGET_COUNTER_INPUT_BASE']+6,20),('team-without-landings',L['LANDING_META_BASE'],0),
  ('team-header-magic',L['WORLD_TEAM_INPUT_BASE'],0),('team-header-version',L['WORLD_TEAM_INPUT_BASE']+1,2),
  ('team-binding-count',L['WORLD_TEAM_INPUT_BASE']+2,4),('team-parts-boolean',L['WORLD_TEAM_INPUT_BASE']+3,2),
  ('team-reserved',L['WORLD_TEAM_INPUT_BASE']+4,1),('team-source-owner',L['WORLD_TEAM_INPUT_BASE']+8,6),
  ('team-budget-zero',L['WORLD_TEAM_INPUT_BASE']+9,0),('team-budget-overflow',L['WORLD_TEAM_INPUT_BASE']+9,257),
  ('team-budget-split',L['WORLD_TEAM_INPUT_BASE']+11,2),('team-attacker-order',L['DEFINITION_BASE']+F['OWNER'],1),
  ('team-unused-binding',L['WORLD_TEAM_INPUT_BASE']+8+5*2,1),('team-group-inconsistent-source',L['WORLD_TEAM_INPUT_BASE']+10,4),
  ('team-missing-event-mask',L['EVENT_CANDIDATE_BASE']+44*L['MASK_WORDS'],0)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args()
 rows,programs,bad=prepare();observed=[inspect_native(c) for c in rows];native=[n for n,t in observed]
 if a.cpu_only:print('Team part/body native',len(rows),'raw',len(bad),'GPU0');return
 packed=array.array('I',[len(rows)+len(bad)])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();ow=OUTPUT*4
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();e=json.loads((folder/'evidence.json').read_text());assert e['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-team-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(SOURCE,'portableEvents',data,INPUT,OUTPUT,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 checked=[]
 for i,(c,(_,m,b),n) in enumerate(zip(rows,programs,native)):
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  try:
   r=decoded(block,m,c,b);changed=[k for k in n if k!='scope' and r[k]!=n[k]];trace=skill_trace(block,m)
   if trace!=observed[i][1]:changed.append('skill_trace')
  except Exception as error:r=dict(error=repr(error));changed=['decode'];trace=[]
  checked.append(dict(name=c['name'],passed=block[0]==0 and not changed,status=block[0],changed=changed,actual=r,native=n,skill_trace=trace,native_skill_trace=observed[i][1]))
 rejected=[dict(name=name,status=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little'),passed=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little')==64) for i,(name,_) in enumerate(bad)]
 report=dict(passed=all(c['passed'] for c in checked+rejected),cases=checked,rejected_cases=rejected,captured=str(folder),evidence=e,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),unchanged_gpu_retries=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-team-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[(c['name'],c.get('changed'),c['status']) for c in checked+rejected if not c['passed']];print('Team part/body',len(rows),'native',len(bad),'raw',a.backend)
if __name__=='__main__':main()
