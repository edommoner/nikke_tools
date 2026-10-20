"""Common frame registry versus native BossScript/ActorRegistry lifecycle.
This phase checks identities,open generations,expiry and parent queries;actor
HP,landing,enemy-count policies,interrupt adapter and public admission stay closed.
"""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
import engine_worker
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L
from portable_actor_specs import compile_registry,NONE
from calculator.boss_pattern import BossScript,validate
from world_actor_runtime import registry_for
from impact_specs import ActorHandle,ActorKind

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
body=module('registry_body','research/verify-world-overlay-body.py');SOURCE='gpu/world_actor_entry.slang'
def cases():
 rows=[]
 def add(name,patterns,queries,duration=.5):rows.append(dict(name=name,patterns=patterns,queries=queries,duration=duration))
 parts=lambda id='parts',**kw:dict(id=id,kind='parts',targets=[dict(name=id+'-right',hp=10),dict(name=id+'-left',hp=10)],**kw)
 wave=lambda id='wave',count=2,**kw:dict(id=id,kind='summon',spec=dict(name='adds',count=count,hp=13),**kw)
 add('configured-body-part-add-order',[wave(),parts()],[(0,0,0,1,0),(0,1,0,1,0),(0,1,1,1,1),(0,5,1,1,0)])
 add('not-spawned-does-not-alias-body',[wave(delay=.2),parts(delay=.2)],[(0,5,0,1,0),(.1,1,0,1,1),(.25,5,0,1,0)])
 add('expired-generation-stays-queryable',[wave(until={'time':.2}),parts(until={'time':.2})],[(.1,1,0,1,0),(.25,1,0,1,0),(.25,1,0,1,1),(.25,5,1,1,0)])
 add('respawn-stale-handles-rejected',[wave(after=['start','wave'],repeat=0,until={'time':.1})],[(.05,5,0,1,0),(.25,5,0,1,0),(.25,5,0,3,0),(.4,5,0,4,0)])
 add('part-parent-survives-reopening',[parts(after=['start','parts'],repeat=0,until={'time':.1})],[(.05,1,1,1,1),(.25,1,1,3,1),(.25,1,1,1,1)])
 add('declaration-order-differs-from-type-order',[wave('first'),parts('middle'),wave('last')],[(0,5,0,1,0),(0,5,3,1,0),(0,1,1,1,0)])
 add('unknown-kind-and-identity',[wave()],[(0,1,0,1,0),(0,5,9,1,0),(0,2,0,1,0),(0,0,1,1,1)])
 add('body-exact-generation',[dict(id='open',kind='idle')],[(0,0,0,1,0),(0,0,0,2,0)])
 add('128-actors-127-adds',[wave(count=127)],[(0,5,126,1,0),(0,5,127,1,0)])
 p=parts();p['targets']=[dict(name='part-'+str(i),hp=10) for i in range(127)]
 add('128-actors-127-parts',[p],[(0,1,126,1,0),(0,1,126,1,1)])
 add('all32-node-bindings',[wave('wave'+str(i),count=3) for i in range(32)],[(0,5,0,1,0),(0,5,95,1,0)])
 add('parent-root-after-expiry',[parts(until={'time':.1})],[(.25,1,1,1,1),(.25,1,1,2,1)])
 return rows

def compile_case(case):
 patterns=validate(copy.deepcopy(case['patterns']),squad_size=5);payload,bindings=compile_registry(patterns)
 c=copy.deepcopy(body.cases()[0]);c['name']=case['name'];c['duration']=case['duration'];c['patterns']=[dict({k:v for k,v in p.items() if k in ('id','after','delay','until','repeat','emit','emit_end')},kind='idle') if p['kind'] in ('parts','summon') else copy.deepcopy(p) for p in case['patterns']]
 for w in c['combat']['weapons']:w['enabled']=False
 words,meta=body.compile_case(c);words[0]=L['WORLD_ACTOR_ABI'];words.extend(payload)
 commands=[]
 for index,(time,kind,identity,generation,root) in enumerate(case['queries']):
  commands.extend([[time,24,0,0,0,0,0],[time,33,kind,identity,generation,root,index]])
 commands.append([case['duration'],24,0,0,0,0,0]);assert len(commands)<=L['COMMANDS'];words[2]=len(commands)
 words[L['COMMAND_BASE']:L['COMMAND_BASE']+L['COMMANDS']*8]=[0]*(L['COMMANDS']*8)
 for i,(time,op,*args) in enumerate(commands):
  at=L['COMMAND_BASE']+i*8;row=[op,*struct.unpack('<II',struct.pack('<d',time)),*(v&NONE for v in args)];assert len(row)==8;words[at:at+8]=row
 assert len(words)==L['WORLD_ACTOR_INPUT_WORDS'];return words,bindings

def native(case):
 patterns=validate(copy.deepcopy(case['patterns']),squad_size=5);_,bindings=compile_registry(patterns);enemy={'def':0,'core_px':0};boss=BossScript(patterns,enemy,lambda *_:False);registry=registry_for(SimpleNamespace(),boss);answers=[];time=0.
 def advance(through):
  nonlocal time
  while time<=through:
   boss.begin_frame(time,enemy);time+=1/60
 for through,kind,identity,generation,root in case['queries']:
  advance(through)
  try:snapshot=registry.root(ActorHandle(kind,identity,generation)) if root else registry.exact(ActorHandle(kind,identity,generation))
  except ValueError as error:
   text=str(error);status=3 if 'Stale' in text else 2 if 'not spawned' in text else 1;answers.append([status]+[0]*7)
  else:
   h=snapshot.handle;p=snapshot.parent;answers.append([0,int(h.kind),h.identity,h.generation,int(snapshot.alive),int(p.kind) if p else NONE,p.identity if p else NONE,p.generation if p else 0])
 advance(case['duration']);boss.finish(case['duration']);final=[]
 for b in bindings:
  run=boss._runs[b.run] if b.run>=0 else None;generation=run.opens if run else 1;alive=bool(run.active) if run else True
  final.append([int(b.kind),b.identity,generation,int(alive),int(b.parent.kind) if b.parent else NONE,b.parent.identity if b.parent else NONE,b.parent.generation if b.parent else 0,b.run if b.run>=0 else NONE])
 return dict(count=len(bindings),queries=answers,registry=final)

def negatives(programs):
 seed=programs[0][0];base=L['WORLD_ACTOR_INPUT_BASE'];binding=L['WORLD_ACTOR_BINDING_BASE'];node=L['WORLD_ACTOR_NODE_BASE'];rows=[]
 for name,at,value in [('bad-magic',base,0x57413032),('empty-registry',base+1,0),('capacity129',base+1,129),('wrong-node-count',base+2,1),('reserved-header',base+7,1),('bad-source-kind',node,3),('empty-source-count',node+1,0),('unused-node',node+31*4,1),('bad-body-kind',binding,5),('bad-body-generation-source',binding+3,0),('bad-body-parent',binding+5,0),('noncanonical-part-id',binding+8+1,9),('wrong-source-slot',binding+8+4,1),('cyclic-part-parent',binding+8+5,1),('reserved-binding',binding+8+7,1),('unused-binding',binding+127*8,1),('disabled-nonzero-payload',base,0)]:
  words=list(seed);words[at]=value;rows.append((name,words))
 query=L['COMMAND_BASE']+8
 for name,at,value in [('query-generation-zero',query+5,0),('query-invalid-kind',query+3,6),('query-identity-overflow',query+4,0x10000000),('query-invalid-root',query+6,2),('query-output-overflow',query+7,L['COMMANDS'])]:
  words=list(seed);words[at]=value;rows.append((name,words))
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');args=p.parse_args();fixtures=cases();programs=[compile_case(c) for c in fixtures];bad=negatives(programs);old=json.loads((ROOT/'research/portable-world-charge-hold-expected.json').read_text());old_report=json.loads((ROOT/'research/portable-world-overlay-charge-hold-metal.json').read_text());olddata=(Path(old_report['captured'])/'input.bin').read_bytes();oldiw=L['WORLD_OVERLAY_INPUT_WORDS']*4;oldrows=old['comparison']['cases'];assert len(oldrows)==208
 packed=array.array('I',[len(programs)+len(bad)+208])
 for words,_ in programs:packed.extend(words)
 for _,words in bad:packed.extend(words)
 for i,c in enumerate(oldrows):
  raw=olddata[4+i*oldiw:4+(i+1)*oldiw];assert hashlib.sha256(raw).hexdigest()==c['input_sha256'];words=list(struct.unpack('<'+'I'*L['WORLD_OVERLAY_INPUT_WORDS'],raw));assert words[0]==L['WORLD_OVERLAY_ABI'];words[0]=L['WORLD_ACTOR_ABI'];words.extend([0]*(L['WORLD_ACTOR_INPUT_WORDS']-L['WORLD_OVERLAY_INPUT_WORDS']));packed.extend(words)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();folder=ROOT/'research/portable-build'/('world-actors-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
 try:raw,evidence=execute(SOURCE,'portableEvents',data,L['WORLD_ACTOR_INPUT_WORDS'],L['WORLD_FRAME_OUTPUT_WORDS'],args.backend)
 except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,c in enumerate(fixtures):
  block=values[i*L['WORLD_FRAME_OUTPUT_WORDS']:(i+1)*L['WORLD_FRAME_OUTPUT_WORDS']];count=len(programs[i][1]);base=L['WORLD_ACTOR_STATE_BASE'];query=L['WORLD_ACTOR_QUERY_BASE'];actual=dict(count=block[base],queries=[list(block[query+j*8:query+(j+1)*8]) for j in range(len(c['queries']))],registry=[list(block[base+8+j*8:base+8+(j+1)*8]) for j in range(count)]);expected=native(c);results.append(dict(name=c['name'],passed=block[0]==0 and actual==expected,status=block[0],actual=actual,native=expected))
 rejected=[dict(name=name,status=values[(len(programs)+i)*L['WORLD_FRAME_OUTPUT_WORDS']],passed=values[(len(programs)+i)*L['WORLD_FRAME_OUTPUT_WORDS']]==64) for i,(name,_) in enumerate(bad)]
 prior=[];ow=L['WORLD_FRAME_OUTPUT_WORDS']*4
 for i,c in enumerate(oldrows):
  at=(len(programs)+len(bad)+i)*ow;h=hashlib.sha256(raw[at:at+ow]).hexdigest();prior.append(dict(name=c['name'],passed=h==c['output_sha256'],output_sha256=h,expected_sha256=c['output_sha256']))
 report=dict(passed=all(x['passed'] for x in results+rejected+prior),cases=results,rejected_cases=rejected,preserved208=prior,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),captured=str(folder),evidence=evidence,scope='128 typed registry identities/parent roots/generations driven by common GPU world frame versus actual native BossScript and ActorRegistry;not full battle/HP/landing certification',actor_hp_landing_connected=False,actor_enemy_count_policy_connected=False,full_character_verified=0,normal_ui='CPU',full_goal_complete=False)
 (ROOT/f'research/portable-world-actors-{args.backend}.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],[x['name'] for x in results+rejected+prior if not x['passed']];print('Actor lifecycle',len(results),'native,raw',len(rejected),'old208 full outputs preserved',args.backend)
if __name__=='__main__':main()
