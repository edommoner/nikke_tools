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
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args()
 rows,programs,bad=prepare();native=[inspect_native(c) for c in rows]
 if a.cpu_only:print('Periodic full native',len(rows),'raw',len(bad),'GPU0');return
 old=json.loads((ROOT/'research/portable-world-pending-metal.json').read_text());p=Path(old['captured']);before=(p/'input.bin').read_bytes();prior=(p/'readback.bin').read_bytes();assert old['passed'] and int.from_bytes(before[:4],'little')==878 and sha(before)==old['evidence']['input_sha256'] and sha(prior)==old['evidence']['output_sha256']
 iw=97464*4;ow=OUTPUT*4;legacy=524288*4;count=len(rows)+len(bad)+878;packed=array.array('I',[count])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(878):
  w=list(struct.unpack_from('<'+'I'*97464,before,4+i*iw));w[0]=L['WORLD_PERIODIC_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-periodic-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data);parts=[];runs=[]
  # Both buffers stay below 2GiB. Inputs are disjoint, with no retries.
  for begin in range(0,count,700):
   n=min(700,count-begin);batch=n.to_bytes(4,'little')+data[4+begin*iw:4+(begin+n)*iw];(folder/f'input-{begin}.bin').write_bytes(batch)
   try:part,e=execute(SOURCE,'portableEvents',batch,97464,OUTPUT,a.backend)
   except Exception as error:(folder/f'failure-{begin}.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
   (folder/f'readback-{begin}.bin').write_bytes(part);(folder/f'evidence-{begin}.json').write_text(json.dumps(e,indent=2)+'\n');parts.append(part);runs.append(e)
  assert all(e['source_sha256']==runs[0]['source_sha256'] and e['generated_sha256']==runs[0]['generated_sha256'] and e['gpu_execution_verified'] for e in runs)
  raw=b''.join(parts);del parts
  evidence=dict(backend=a.backend,source_sha256=runs[0]['source_sha256'],generated_sha256=runs[0]['generated_sha256'],gpu_execution_verified=True,input_sha256=sha(data),output_sha256=sha(raw),transport=dict(backend=a.backend,cases=count,command_status='completed',dispatches=len(runs),batches=[e['transport'] for e in runs]))
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 checked=[]
 for i,(case,(_,meta,bindings),(expected,expected_trace)) in enumerate(zip(rows,programs,native)):
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  try:
   actual=decoded(block,meta,case,bindings);trace=skill_trace(block);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
   if trace!=expected_trace:changed.append('skill_trace')
   restored=not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]);assert block[L['WORLD_PERIODIC_HEAD_BASE']]==0x57504331
   for row in range(256):snapshot(block,L['WORLD_PERIODIC_DEFINITION_BASE']+row*38)
   for receipt in range(L['LANDINGS']):snapshot(block,L['WORLD_PERIODIC_PACKET_BASE']+receipt*38)
  except Exception as error:actual=dict(error=repr(error));trace=[];changed=['decode'];restored=False
  checked.append(dict(name=case['name'],passed=block[0]==0 and not changed and restored,status=block[0],changed=changed,context_restored=restored,actual=actual,native=expected,skill_trace=trace,native_skill_trace=expected_trace))
 rejected=[dict(name=name,status=int.from_bytes(raw[(len(rows)+j)*ow:(len(rows)+j)*ow+4],'little'),passed=int.from_bytes(raw[(len(rows)+j)*ow:(len(rows)+j)*ow+4],'little')==64) for j,(name,_) in enumerate(bad)]
 offset=len(rows)+len(bad);zero=b'\0'*(ow-legacy);kept=[dict(index=j,passed=raw[(offset+j)*ow:(offset+j)*ow+legacy]==prior[j*legacy:(j+1)*legacy] and raw[(offset+j)*ow+legacy:(offset+j+1)*ow]==zero) for j in range(878)]
 result=dict(passed=all(c['passed'] for c in checked+rejected+kept),cases=checked,rejected_cases=rejected,preserved878=kept,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),input_words=97464,output_words=OUTPUT,unchanged_gpu_retries=0,cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-periodic-{a.backend}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');assert result['passed'],[c.get('name',c.get('index')) for c in checked+rejected+kept if not c['passed']];print('Periodic native',len(rows),'raw',len(bad),'old878 prefixes and zero extension exact',a.backend)
if __name__=='__main__':main()
