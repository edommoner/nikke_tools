"""Full native shared recipient contracts;one executable for CUDA and Metal."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_removal_specs import plan
import world_actor_recipient_cases as cases
s=importlib.util.spec_from_file_location('recipient_state',ROOT/'research/verify-world-actor-state.py');state=importlib.util.module_from_spec(s);s.loader.exec_module(state)
SOURCE='gpu/world_actor_recipient_entry.slang';MAGIC=0x57523031

def fixtures():return cases.fixtures(state)
def compile_case(c):
 w,m,b=state.compile_case(c);w[0]=L['WORLD_ACTOR_RECIPIENT_ABI'];w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC
 for i,e in enumerate(c['effects']):
  p=plan(e,combat=c['combat'])
  if p is not None and p[0]==2 and p[1][0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b

def decoded(block,meta,c,bindings):
 old=array.array('I',block[:262144]);rows=[];members=[]
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for j in range(block[9]):
  p=L['CARRIER_STATE_BASE']+j*L['CARRIER_WORDS'];slot,definition=block[p:p+2];key=L['WORLD_ACTOR_FIELD_KEY_BASE']+slot*4
  if block[key]&0x80000000:old[key:key+4]=array.array('I',[0]*4)
  if not block[p+4]&1:continue
  at=L['WORLD_ACTOR_RECIPIENT_BASE']+16+slot*L['WORLD_ACTOR_RECIPIENT_WORDS'];kind,count=block[at:at+2]
  if kind==0:continue
  handles=[];live=[]
  for i in range(count):
   target=(block[at+136+i//4]>>((i%4)*8))&255;b=bindings[target];h=[int(b.kind),b.identity,block[at+8+target]];handles.append(h)
   if block[at+2+target//32]&(1<<(target%32)):live.append(h)
  row=dict(name=c['effects'][definition]['name'],owner=c['owners'][definition],stack=block[p+3],activated=number(p+7),end=number(p+5))
  if len(handles)==1:row['actor']=handles[0]
  else:row['actors']=handles
  rows.append(row);members.append(live)
 actual=state.decoded(old,meta,c,bindings);actual['enemy_fields']['carriers']=rows;actual['enemy_fields']['recipient_memberships']=members;return actual

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0]
 for name,at,value in [('unknown-recipient-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57523032),('shared-init-disabled-in-mutation-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x574D3031),('init-definition-index-overflow',L['MODE_BASE']+32+4,257),('init-nonfinite-value',L['DEFINITION_BASE']+32+7,0x7ff00000)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();native=[state.fields.pool.observe(c) for c in rows]
 if a.cpu_only:
  (ROOT/'research/portable-build/world-actor-recipient-native.json').write_text(json.dumps(dict(names=[c['name'] for c in rows],cases=native),ensure_ascii=False,indent=2)+'\n');print('CPU shared recipient native',len(rows),'raw',len(bad),'GPU calls0');return
 old=json.loads((ROOT/'research/portable-world-actor-mutation-metal.json').read_text());op=Path(old['captured']);before=(op/'input.bin').read_bytes();beforeout=(op/'readback.bin').read_bytes();n=int.from_bytes(before[:4],'little');assert n==461;iw=92336*4;ow=524288*4;oldow=262144*4
 packed=array.array('I',[len(rows)+len(bad)+n])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(n):
  w=list(struct.unpack_from('<'+'I'*92336,before,4+i*iw));w[0]=L['WORLD_ACTOR_RECIPIENT_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data and evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-actor-recipient-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,92336,524288,a.backend)
  except Exception as err:(folder/'failure.json').write_text(json.dumps(dict(error=repr(err),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(c,(_,m,b),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*524288:(i+1)*524288]
  try:actual=decoded(block,m,c,b);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
  except Exception as err:actual=dict(status=block[0],decode_error=repr(err));changed=['decode']
  results.append(dict(name=c['name'],passed=block[0]==0 and not changed,changed=changed,actual=actual,native=expected))
 rejected=[dict(name=name,status=values[(len(rows)+j)*524288],passed=values[(len(rows)+j)*524288]==64) for j,(name,_) in enumerate(bad)]
 prior=[]
 for j in range(n):
  i=len(rows)+len(bad)+j;now=raw[i*ow:(i+1)*ow];prior.append(dict(index=j,passed=now[:oldow]==beforeout[j*oldow:(j+1)*oldow] and not any(now[oldow:])))
 report=dict(passed=all(x['passed'] for x in results+rejected+prior),cases=results,rejected_cases=rejected,preserved461=prior,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-actor-recipient-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[x.get('name',x.get('index')) for x in results+rejected+prior if not x['passed']];print('Persistent recipient native',len(rows),'raw',len(bad),'old461 exact',a.backend)
if __name__=='__main__':main()
