"""Canonical enemy carriers/128 recipient snapshots versus actual full native simulate."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_actor_pool_specs import compile_pools
from portable_world_schedule_specs import compile_schedule
from portable_enemy_specs import enemy_buff_plan
import world_actor_fields_cases as cases

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pool=module('fields_pool','research/verify-world-actor-pools.py');SOURCE='gpu/world_actor_fields_entry.slang'
def fixtures():return cases.fixtures(pool)
def compile_case(c):
 words,meta,bindings=pool.compile_case(c);_,patterns=compile_schedule(dict(patterns=c['patterns'],clock='accumulated',duration=c['duration']),notice_payload=True)
 words[0]=L['WORLD_ACTOR_FIELDS_ABI'];words[L['WORLD_ACTOR_POOL_INPUT_BASE']:]=compile_pools(patterns,bindings,fields=True,boss_atk=c['enemy'].get('atk',114344),focus_aim=bool(words[L['WORLD_META_BASE']+4]),armed=any(words[L['WEAPON_BASE']+i*L['WEAPON_WORDS']] and words[L['WEAPON_BASE']+i*L['WEAPON_WORDS']+1]==0 for i in range(5)))
 for i,e in enumerate(c['effects']):
  plan=enemy_buff_plan(e)
  if plan is not None and plan[0]==2:words[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 step=words[2]
 for index,(who,kind,id,gen) in enumerate(c.get('field_queries',[])):
  words[L['COMMAND_BASE']+step*8:L['COMMAND_BASE']+(step+1)*8]=[39,*struct.unpack('<II',struct.pack('<d',c['duration'])),who,kind,id,gen,index];step+=1
 assert step<64;words[2]=step+1;words[L['COMMAND_BASE']+step*8:L['COMMAND_BASE']+(step+1)*8]=[40,*struct.unpack('<II',struct.pack('<d',c['duration'])),0,0,0,0,0]
 assert len(words)==L['WORLD_ACTOR_POOL_INPUT_WORDS'];return words,meta,bindings

def decoded(block,meta,c,bindings):
 actual=pool.decoded(block,meta,c,bindings);carriers=[]
 num=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for j in range(block[9]):
  at=L['CARRIER_STATE_BASE']+j*L['CARRIER_WORDS'];slot,definition=block[at:at+2];key=L['WORLD_ACTOR_FIELD_KEY_BASE']+slot*4
  if not block[at+4]&1 or block[key]==0:continue
  if enemy_buff_plan(c['effects'][definition]) is None:continue
  actor=bindings[block[key]-1];end=num(at+5)
  carriers.append(dict(name=c['effects'][definition]['name'],owner=c['owners'][definition],actor=[int(actor.kind),actor.identity,block[key+1]],stack=block[at+3],activated=num(at+7),end=end))
 actual['enemy_fields']=dict(queries=[list(block[L['WORLD_ACTOR_FIELD_ALL_BASE']+i*12:L['WORLD_ACTOR_FIELD_ALL_BASE']+(i+1)*12]) for i in range(len(bindings))],carriers=carriers,explicit_queries=[list(block[L['WORLD_ACTOR_FIELD_QUERY_BASE']+i*16:L['WORLD_ACTOR_FIELD_QUERY_BASE']+(i+1)*16]) for i in range(len(c.get('field_queries',[])))],owned_snapshots=block[L['WORLD_ACTOR_POOL_OUTPUT_BASE']+7])
 return actual

def negative_inputs(programs):
 rows=[];seed=programs[0][0];d=L['DEFINITION_BASE'];cond=L['CONDITION_BASE'];hp=L['WORLD_ACTOR_POOL_DEF_BASE']+12
 for name,at,value in [('unsupported-enemy-stat',d+2,0),('unsupported-condition',d+27,1),('enemy-recipient-scope-notification',L['HEALTH_DEFINITION_BASE']+2,3),('enemy-count-route-overflow',L['DAMAGE_DEFINITION_BASE']+1,257),('enemy-selector-overflow',L['DAMAGE_DEFINITION_BASE'],10),('nonfinite-boss-attack',L['WORLD_ACTOR_POOL_INPUT_BASE']+3,0x7ff00000),('negative-add-attack',hp+10,0xbff00000),('unused-actor-attack',hp+120*12+9,1),('reserved-pool-header',L['WORLD_ACTOR_POOL_INPUT_BASE']+7,1)]:
  w=list(seed);w[at]=value
  if name=='unsupported-condition':w[cond]=18
  rows.append((name,w))
 # Query boundaries and disabled payload are rejected by the same GPU entry.
 for name,arg,value in [('snapshot-owner-overflow',3,5),('snapshot-reserved-word',7,1)]:
  w=list(seed);at=L['COMMAND_BASE']+(w[2]-1)*8+arg;w[at]=value;rows.append((name,w))
 countcase=next(c for c in fixtures() if c['name']=='count-inclusive-above-4');cw,_,_=compile_case(countcase)
 for name,lo,hi in [('nan-count',0,0x7ff80000),('fractional-count',0,0x3fe00000),('overflow-count',0,0x41e00000)]:
  w=list(cw);w[L['CONDITION_BASE']+2:L['CONDITION_BASE']+4]=[lo,hi];rows.append((name,w))
 capacity=next(c for c in fixtures() if c['name']=='512-resident-capacity-with128-receivers');capacity['effects'].append(dict(capacity['effects'][0],name='fifth'));capacity['owners'].append(0);w,_,_=compile_case(capacity);rows.append(('640-recipient-carriers-exceed512-capacity',w))
 for name,arg,value in [('query-owner-overflow',3,5),('query-kind-overflow',4,6),('query-id-overflow',5,0x10000000),('query-zero-generation',6,0),('query-output-overflow',7,64)]:
  w=list(seed);at=L['COMMAND_BASE']+(w[2]-1)*8;w[at:at+8]=[39,*w[at+1:at+3],0,5,0,1,0];w[at+arg]=value;rows.append((name,w))
 return rows

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];return rows,programs,negative_inputs(programs)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();native=[pool.observe(c) for c in rows]
 if a.cpu_only:
  (ROOT/'research/portable-build/world-actor-fields-native.json').write_text(json.dumps(dict(names=[c['name'] for c in rows],cases=native),ensure_ascii=False,indent=2)+'\n');print('CPU full native fields/count/ranks',len(rows),'literal inputs;GPU calls0');return
 old=json.loads((ROOT/'research/portable-world-actor-pools-metal.json').read_text());oldp=Path(old['captured']);olddata=(oldp/'input.bin').read_bytes();oldraw=(oldp/'readback.bin').read_bytes();assert int.from_bytes(olddata[:4],'little')==285
 iw=L['WORLD_ACTOR_POOL_INPUT_WORDS']*4;ow=L['WORLD_ACTOR_FIELDS_OUTPUT_WORDS']*4;oldow=L['WORLD_ACTOR_POOL_OUTPUT_WORDS']*4
 packed=array.array('I',[len(rows)+len(bad)+285])
 for words,_,_ in programs:packed.extend(words)
 for _,words in bad:packed.extend(words)
 for i in range(285):
  words=list(struct.unpack_from('<'+'I'*L['WORLD_ACTOR_POOL_INPUT_WORDS'],olddata,4+i*iw));words[0]=L['WORLD_ACTOR_FIELDS_ABI'];packed.extend(words)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data and evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-actor-fields-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,L['WORLD_ACTOR_POOL_INPUT_WORDS'],L['WORLD_ACTOR_FIELDS_OUTPUT_WORDS'],a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 stride=ow//4;results=[]
 for i,(c,(_,meta,bindings),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*stride:(i+1)*stride]
  try:actual=decoded(block,meta,c,bindings);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
  except Exception as error:actual=dict(status=block[0],decode_error=repr(error));changed=['decode']
  results.append(dict(name=c['name'],passed=block[0]==0 and not changed,changed=changed,actual=actual,native=expected))
 rejected=[dict(name=n,status=values[(len(rows)+i)*stride],passed=values[(len(rows)+i)*stride]==64) for i,(n,_) in enumerate(bad)]
 prior=[]
 for j in range(285):
  i=len(rows)+len(bad)+j;before=oldraw[j*oldow:(j+1)*oldow];current=raw[i*ow:(i+1)*ow];extra=current[oldow:];magic=0x57463031 if int.from_bytes(before[L['WORLD_ACTOR_POOL_OUTPUT_BASE']*4:(L['WORLD_ACTOR_POOL_OUTPUT_BASE']+1)*4],'little')==0x57485031 else 0;tail_ok=int.from_bytes(extra[:4],'little')==magic and not any(extra[4:]);prior.append(dict(index=j,passed=current[:oldow]==before and tail_ok,legacy_prefix_exact=current[:oldow]==before,new_fields_tail_valid=tail_ok,output_sha256=hashlib.sha256(current).hexdigest()))
 report=dict(passed=all(x['passed'] for x in results+rejected+prior),cases=results,rejected_cases=rejected,preserved285=prior,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),gpu_readback_reused=a.replay is not None,cpu_state_used_as_input=False,full_character_verified=0,canonical_world_admission=False,normal_ui='CPU',full_goal_complete=False)
 (ROOT/f'research/portable-world-actor-fields-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[x.get('name',x.get('index')) for x in results+rejected+prior if not x['passed']];print('Full native fields',len(rows),'raw',len(bad),'prior285 exact',a.backend)
if __name__=='__main__':main()
