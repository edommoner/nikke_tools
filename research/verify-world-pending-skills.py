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
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args()
 rows,programs,bad=prepare();native=[inspect_native(c) for c in rows]
 if a.cpu_only:print('Pending full native',len(rows),'raw',len(bad),'GPU0');return
 old=[]
 for report,count in [('portable-world-skill-metal.json',833),('portable-world-skill-formula-metal.json',8)]:
  r=json.loads((ROOT/'research'/report).read_text());p=Path(r['captured']);before=(p/'input.bin').read_bytes();prior=(p/'readback.bin').read_bytes();assert r['passed'] and int.from_bytes(before[:4],'little')==count and hashlib.sha256(before).hexdigest()==r['evidence']['input_sha256'] and hashlib.sha256(prior).hexdigest()==r['evidence']['output_sha256'];old.append((report,count,before,prior))
 iw=97464*4;ow=524288*4;packed=array.array('I',[len(rows)+len(bad)+841])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for _,count,before,_ in old:
  for i in range(count):
   w=list(struct.unpack_from('<'+'I'*97464,before,4+i*iw));w[0]=L['WORLD_PENDING_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-pending-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,97464,524288,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 checked=[]
 for i,(case,(_,meta,bindings),(expected,expected_trace)) in enumerate(zip(rows,programs,native)):
  block=values[i*524288:(i+1)*524288]
  try:
   actual=decoded(block,meta,case,bindings);trace=skill_trace(block);changed=[k for k in expected if k!='scope' and expected[k]!=actual[k]]
   if trace!=expected_trace:changed.append('skill_trace')
   restored=not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096])
  except Exception as error:actual=dict(error=repr(error));trace=[];changed=['decode'];restored=False
  checked.append(dict(name=case['name'],passed=block[0]==0 and not changed and restored,status=block[0],changed=changed,context_restored=restored,actual=actual,native=expected,skill_trace=trace,native_skill_trace=expected_trace))
 rejected=[dict(name=n,status=values[(len(rows)+j)*524288],passed=values[(len(rows)+j)*524288]==64) for j,(n,_) in enumerate(bad)];offset=len(rows)+len(bad);kept=[]
 for report,count,_,prior in old:
  for j in range(count):kept.append(dict(source=report,index=j,passed=raw[(offset+j)*ow:(offset+j+1)*ow]==prior[j*ow:(j+1)*ow]))
  offset+=count
 r=dict(passed=all(x['passed'] for x in checked+rejected+kept),cases=checked,rejected_cases=rejected,preserved841=kept,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,same_frame_pending_actor_landing=True,ordinary_queue_not_drained_by_pending=True,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-pending-{a.backend}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');assert r['passed'],[x.get('name',x.get('index')) for x in checked+rejected+kept if not x['passed']];print('Pending native',len(rows),'raw',len(bad),'old841 all words exact',a.backend)
if __name__=='__main__':main()
