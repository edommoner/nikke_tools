"""Shared CUDA/Metal Actor HP and physical landing versus complete native battles."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L
from portable_actor_specs import compile_registry
from portable_actor_pool_specs import compile_pools
from portable_world_schedule_specs import compile_schedule
from world_frame_native import observe
import world_actor_pool_cases as manual

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
body=module('pool_body','research/verify-world-overlay-body.py');SOURCE='gpu/world_actor_pool_entry.slang'
def fixtures():
 base=copy.deepcopy(body.cases()[0]);base.update(observe_overlay=True,observe_actor_pools=True,element_codes=['작열']*5)
 rows=[]
 def add(name,patterns,duration=.5):
  c=copy.deepcopy(base);c.update(name=name,patterns=patterns,duration=duration);rows.append(c);return c
 def wave(count=3,**spec):return dict(id='wave',kind='summon',spec=dict(count=count,name='adds',**spec))
 add('hp-clips-overkill-reaims-same-frame',[wave(hp=1300)])
 add('hit-hp-two-hits',[wave(hit_hp=2)])
 add('hp-switches-to-hit-hp',[wave(hp=100000,hit_hp=2,hit_hp_after=.2)])
 add('hit-hp-zero-damage-still-counts',[wave(hit_hp=2)])['base_atk']=[0]*5
 p=wave(hp=1300);p.update(after=['start','wave'],repeat=0,until=dict(targets_cleared=True));add('gpu-cleared-reopens-generations',[p])
 p=wave(hp=100000);p.update(delay=.15,until=dict(time=.15));add('delayed-spawn-and-expiry',[p])
 c=add('pellets-muzzles-retarget-every-land',[wave(count=7,hp=1300)])
 for w in c['combat']['weapons']:w.update(pellets=3,muzzles=2)
 c=add('128-actors-live-127-adds',[wave(count=127,hp=1300)],3.)
 c=add('death-notice-allied-buff-next-frame',[wave(count=5,hp=1300)])
 c['effects']=[body.f.effect('atk_pct',20,target='all_allies',trigger=dict(timing=['enemy_death'],condition=[]))];c['owners']=[0]
 for kind in ('shield','vanish'):
  c=add(kind+'-adds-bypass-boss-gate',[wave(hp=1300),dict(id='gate',kind=kind,until=dict(time=.25),**(dict(code='수냉') if kind=='shield' else {}))]);c['camera']=list(body.f.NAMES);c['camera_mode']='shared'
 c=add('vanish-unobserved-adds-still-pause',[wave(hp=1300),dict(id='gate',kind='vanish',until=dict(time=.25))])
 c=add('charge-actual-add-landing',[wave(hp=1300)],1.2);c['weapon_metadata'].update(fire_rate=5,fire_rate_max=5)
 for w in c['combat']['weapons']:w.update(mode='charge',base_weapon_type='SR',charge=.2,interval=.4,min_cycle=.2,full_charge_mult=300,gauge_mult=100)
 add('parts-owned-pools-without-physical-aim',[dict(id='parts',kind='parts',targets=[dict(name='right',hp=3),dict(name='left',hp=0)])])
 return rows

def compile_case(c):
 words,meta=body.compile_case(c,actor_pools=True);_,patterns=compile_schedule(dict(patterns=c['patterns'],clock='accumulated',duration=c['duration']),notice_payload=True)
 table,bindings=compile_registry(patterns,pools=True);words[0]=L['WORLD_ACTOR_POOL_ABI'];words.extend(table);words.extend(compile_pools(patterns,bindings));assert len(words)==L['WORLD_ACTOR_POOL_INPUT_WORDS']
 if 'actions' in c:
  commands=[]
  for t,op,args,amount in c['actions']:commands.extend([(t,24,[0]*5,0),(t,op,args,amount)])
  commands.append((c['duration'],24,[0]*5,0));assert len(commands)<=L['COMMANDS'];words[2]=len(commands)
  words[L['COMMAND_BASE']:L['COMMAND_BASE']+L['COMMANDS']*8]=[0]*(L['COMMANDS']*8)
  for i,(t,op,args,amount) in enumerate(commands):
   at=L['COMMAND_BASE']+i*8;words[at:at+8]=[op,*struct.unpack('<II',struct.pack('<d',t)),*args]
   at=L['WORLD_ACTOR_LAND_INPUT_BASE']+i*2;words[at:at+2]=struct.unpack('<II',struct.pack('<d',amount))
 return words,meta,bindings

def decoded(block,meta,c,bindings):
 patched=array.array('I',block);head=L['WORLD_FRAME_OUTPUT_BASE'];destroy=[]
 for i in range(block[head+2]):
  at=head+2832+i*6
  if block[at]==5:patched[at]=1;destroy.append(i)
 actual=body.read_overlay_result(patched,meta,c);index=0
 for item in actual['boss_log']:
  if item['event']=='down':continue
  # Attack records do not appear in boss_log.
  while block[head+2832+index*6]==3:index+=1
  if index in destroy:item.update(event='destroy',outcome='')
  index+=1
 def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 h=L['WORLD_ACTOR_POOL_OUTPUT_BASE'];p=L['WORLD_ACTOR_POOL_STATE_BASE'];over=L['WORLD_OVERLAY_STATE_BASE'];acct=L['DAMAGE_ACCOUNTING_STATE_BASE']
 actual.update(gauge=actual['ordinary']['queries'][-1]['combat']['gauge'],world_nodes=[dict(blocked=number(over+32+j*8+4),opens=block[over+32+j*8]) for j in range(len(c['patterns']))],actor_pools=dict(pools=[list(block[p+i*16:p+(i+1)*16]) for i in range(len(bindings))],score=block[h+8]+(block[h+9]<<32),spawned=block[h+4],overkill=number(h+16),notice_counts=list(block[h+10:h+14]),pending_notices=block[h+5],deaths=block[h+14]),actor_add_damage=[number(acct+30+i*2) for i in range(5)])
 return actual

def negatives(programs):
 seed=programs[0][0];head=L['WORLD_ACTOR_POOL_INPUT_BASE'];d=L['WORLD_ACTOR_POOL_DEF_BASE']+12;rows=[]
 for name,at,value in [('bad-magic',head,1),('wrong-count',head+1,1),('reserved-header',head+7,1),('invalid-mode',d,5),('nonfinite-hp',d+3,0x7ff00000),('zero-hp',d+3,0),('hit-limit-on-hp',d+1,1),('negative-after',d+5,0xbff00000),('add-death-custom-notice',d+6,1),('reserved-def',d+11,1),('unused-def',d+120*12,1),('disabled-dirty-tail',head,0)]:
  w=list(seed);w[at]=value;rows.append((name,w))
 for name,index,at,value in [('land-negative-amount',14,L['WORLD_ACTOR_LAND_INPUT_BASE']+3,0xbff00000),('land-who-overflow',14,L['COMMAND_BASE']+8+3,5),('land-generation-zero',14,L['COMMAND_BASE']+8+6,0),('land-output-overflow',14,L['COMMAND_BASE']+8+7,64),('query-generation-zero',23,L['COMMAND_BASE']+8+5,0),('set-mask-overflow',17,L['COMMAND_BASE']+8+3,64),('set-capacity-overflow',17,L['COMMAND_BASE']+8+4,32)]:
  w=list(programs[index][0]);w[at]=value;rows.append((name,w))
 return rows

def prepare():
 rows=fixtures();rows+=manual.fixtures(rows[0]);programs=[compile_case(c) for c in rows];bad=negatives(programs);return rows,programs,bad

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);args=ap.parse_args()
 rows,programs,bad=prepare();native=[manual.native(c,L) if 'actions' in c else observe(c) for c in rows]
 if args.cpu_only:
  out=ROOT/'research/portable-build/world-actor-pools-native.json';out.write_text(json.dumps(dict(cases=native,names=[c['name'] for c in rows]),ensure_ascii=False,indent=2)+'\n');print('CPU literal packing and actual full simulate',len(rows),'cases;GPU calls0');return
 old=json.loads((ROOT/'research/portable-world-actors-metal.json').read_text());folder_old=Path(old['captured']);olddata=(folder_old/'input.bin').read_bytes();oldraw=(folder_old/'readback.bin').read_bytes();oldcount=struct.unpack_from('<I',olddata)[0];assert oldcount==242
 packed=array.array('I',[len(rows)+len(bad)+oldcount])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(oldcount):
  w=list(struct.unpack_from('<'+'I'*L['WORLD_ACTOR_INPUT_WORDS'],olddata,4+i*L['WORLD_ACTOR_INPUT_WORDS']*4));w[0]=L['WORLD_ACTOR_POOL_ABI'];w.extend([0]*(L['WORLD_ACTOR_POOL_INPUT_WORDS']-L['WORLD_ACTOR_INPUT_WORDS']));packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if args.replay:
  folder=args.replay;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data;assert evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-actor-pools-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,L['WORLD_ACTOR_POOL_INPUT_WORDS'],L['WORLD_ACTOR_POOL_OUTPUT_WORDS'],args.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 stride=L['WORLD_ACTOR_POOL_OUTPUT_WORDS'];results=[]
 for i,(c,(_,meta,bindings),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*stride:(i+1)*stride]
  try:actual=manual.decoded(block,c,L,bindings) if 'actions' in c else decoded(block,meta,c,bindings);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
  except Exception as error:actual=dict(status=block[0],decode_error=repr(error));changed=['decode']
  results.append(dict(name=c['name'],passed=block[0]==0 and not changed,changed=changed,actual=actual,native=expected))
 rejected=[dict(name=n,status=values[(len(rows)+i)*stride],passed=values[(len(rows)+i)*stride]==64) for i,(n,_) in enumerate(bad)]
 prior=[];ow=L['WORLD_FRAME_OUTPUT_WORDS']*4;nw=stride*4
 for i in range(oldcount):
  start=(len(rows)+len(bad)+i)*nw;block=raw[start:start+nw];before=oldraw[i*ow:(i+1)*ow];prior.append(dict(index=i,passed=block[:ow]==before and not any(block[ow:]),output_sha256=hashlib.sha256(block).hexdigest(),prior_output_sha256=hashlib.sha256(before).hexdigest()))
 report=dict(passed=all(r['passed'] for r in results+rejected+prior),cases=results,rejected_cases=rejected,preserved242=prior,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),full_character_verified=0,normal_ui='CPU',full_goal_complete=False,canonical_world_admission=False)
 out=ROOT/f'research/portable-world-actor-pools-{args.backend}.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[r.get('name',r.get('index')) for r in results+rejected+prior if not r['passed']];print('Actor HP native battles14 + typed pools10,raw',len(bad),'old242 exact',args.backend)
if __name__=='__main__':main()
