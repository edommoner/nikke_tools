"""Typed named predicates and post-notice removal versus the full native engine."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_actor_state_specs import MAGIC,append_queries
import world_actor_state_cases as cases

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fields=module('state_fields','research/verify-world-actor-fields.py');SOURCE='gpu/world_actor_state_entry.slang'
def fixtures():return cases.fixtures(fields)
def compile_case(c):
 words,meta,bindings=fields.compile_case(c);words[0]=L['WORLD_ACTOR_STATE_ABI'];words.extend([0]*(L['WORLD_ACTOR_STATE_INPUT_WORDS']-len(words)));words[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC;meta['_authored_field_queries']=c.get('field_queries',[]);append_queries(words,meta,c.get('state_queries',[]),c['duration']);return words,meta,bindings

def decoded(block,meta,c,bindings):
 actual=fields.decoded(block,meta,c,bindings);number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0];queries=[];allies=[];members=[]
 for q,index in zip(c.get('state_queries',[]),meta['actor_state_query_indices']):
  at=L['WORLD_ACTOR_FIELD_QUERY_BASE']+index*16;r=list(block[at:at+16])
  if r[0]:assert not any(r[1:]);queries.append(dict(status=r[0]));continue
  assert r[5]==meta['states'][q[4]] and not any(r[10:]);queries.append(dict(status=0,kind=r[1],identity=r[2],generation=r[3],alive=bool(r[4]),name=q[4],present=bool(r[6]),stack=number(at+7),enemy_count=r[9]))
 for j in range(block[9]):
  at=L['CARRIER_STATE_BASE']+j*L['CARRIER_WORDS'];slot,definition=block[at:at+2]
  if not block[at+4]&1:continue
  if meta['enemy_buff_definitions'][definition]:members.append(bool(block[at+2]&32));continue
  if c['effects'][definition].get('type')!='buff':continue
  allies.append(dict(name=c['effects'][definition].get('name',''),owner=c['owners'][definition],recipients=None if block[at+4]&2 else [i for i in range(5) if block[at+2]&(1<<i)],stack=block[at+3],activated=number(at+7),end=number(at+5)))
 head=L['WORLD_ACTOR_FIELDS_BASE'];actual['named_state']=dict(queries=queries,allied_carriers=allies,enemy_memberships=members,context_restored=list(block[head+3:head+6])==[0]*3,pending_gone=list(block[head+8:head+12]));return actual

def negative_inputs(programs):
 seed=programs[0][0];rows=[];cond=L['CONDITION_BASE']+L['CONDITION_WORDS'];head=L['WORLD_ACTOR_POOL_INPUT_BASE'];query=next(i for i in range(seed[2]) if seed[L['COMMAND_BASE']+i*8]==41);at=L['COMMAND_BASE']+query*8;side=L['WORLD_ACTOR_STATE_INPUT_BASE']+query*2
 for name,pos,value in [('unknown-policy',head+4,1),('new-condition-without-policy',head+4,0),('condition-name-overflow',cond+1,256),('presence-nonzero-argument',cond+3,0x3ff00000),('nonfinite-condition',cond+3,0x7ff00000),('query-owner-overflow',at+3,5),('query-kind-overflow',at+4,6),('query-id-overflow',at+5,0x10000000),('query-zero-generation',at+6,0),('query-output-overflow',at+7,64),('query-name-overflow',side,256),('query-reserved-flag',side+1,1),('unused-query-sidecar',L['WORLD_ACTOR_STATE_INPUT_BASE']+63*2,1)]:
  w=list(seed);w[pos]=value;rows.append((name,w))
 stack=next(p[0] for p in programs if p[1]['effects'][1]=='conditional' and p[0][cond]==6)
 for name,lo,hi in [('stack-negative',0,0xbff00000),('stack-fractional',0,0x3fe00000),('stack-overflow',0,0x41e00000)]:
  w=list(stack);w[cond+2:cond+4]=[lo,hi];rows.append((name,w))
 for stat in ('max_hp_pct','def_pct'):
  import copy
  c=copy.deepcopy(fixtures()[0]);c['effects']=[fields.pool.body.f.effect(stat,50,target='all_allies',trigger=dict(timing=['passive'],condition=['target_state:missing']))];c['owners']=[0];c['state_queries']=[];w,_,_=compile_case(c);rows.append(('unresolved-runtime-health-'+stat,w))
 return rows

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];return rows,programs,negative_inputs(programs)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();native=[fields.pool.observe(c) for c in rows]
 if a.cpu_only:
  (ROOT/'research/portable-build/world-actor-state-native.json').write_text(json.dumps(dict(names=[c['name'] for c in rows],cases=native),ensure_ascii=False,indent=2)+'\n');print('CPU full native named state',len(rows),'raw',len(bad),'literal inputs;GPU calls0');return
 old=json.loads((ROOT/'research/portable-world-actor-fields-metal.json').read_text());p=Path(old['captured']);olddata=(p/'input.bin').read_bytes();oldraw=(p/'readback.bin').read_bytes();assert int.from_bytes(olddata[:4],'little')==357
 packed=array.array('I',[len(rows)+len(bad)+357])
 for words,_,_ in programs:packed.extend(words)
 for _,words in bad:packed.extend(words)
 for j in range(357):
  words=list(struct.unpack_from('<'+'I'*92208,olddata,4+j*92208*4));words[0]=L['WORLD_ACTOR_STATE_ABI'];words.extend([0]*128);packed.extend(words)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();ow=262144*4
 if a.replay:
  folder=a.replay;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data and evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-actor-state-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,L['WORLD_ACTOR_STATE_INPUT_WORDS'],262144,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(c,(_,meta,bindings),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*262144:(i+1)*262144]
  try:actual=decoded(block,meta,c,bindings);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
  except Exception as error:actual=dict(status=block[0],decode_error=repr(error));changed=['decode']
  results.append(dict(name=c['name'],passed=block[0]==0 and not changed,changed=changed,actual=actual,native=expected))
 rejected=[dict(name=name,status=values[(len(rows)+i)*262144],passed=values[(len(rows)+i)*262144]==64) for i,(name,_) in enumerate(bad)]
 prior=[]
 for j in range(357):
  i=len(rows)+len(bad)+j;now=raw[i*ow:(i+1)*ow];before=oldraw[j*ow:(j+1)*ow];prior.append(dict(index=j,passed=now==before,output_sha256=hashlib.sha256(now).hexdigest()))
 report=dict(passed=all(x['passed'] for x in results+rejected+prior),cases=results,rejected_cases=rejected,preserved357=prior,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-actor-state-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[x.get('name',x.get('index')) for x in results+rejected+prior if not x['passed']];print('Named state',len(rows),'native/raw',len(bad),'old357 exact',a.backend)
if __name__=='__main__':main()
