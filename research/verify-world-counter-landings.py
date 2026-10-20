"""Actual physical counter battles:one Slang source/table for Metal and CUDA."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from world_frame_native import observe,roster_names
s=importlib.util.spec_from_file_location('physical_counter_pack',ROOT/'research/compile-world-target-counter-battles.py');pack=importlib.util.module_from_spec(s);s.loader.exec_module(pack)
SOURCE='gpu/counter_landing_entry.slang'
def fixtures():return pack.fixtures()
compile_case=pack.compile_case
def counter_state(block,case):
 def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 names=roster_names(case);head=L['TARGET_COUNTER_HEAD'];trace=[];resources=[]
 for i in range(block[head+6]):
  at=L['TARGET_COUNTER_TRACE_BASE']+i*24;row=block[at+3];actor=dict(kind=block[at+5],identity=block[at+6],generation=block[at+7]);impact=None
  if block[at+18]:impact=dict(attacker=names[block[at+10]],target=actor,family=block[at+11],outcome=block[at+12],damage=number(at+14),credit=number(at+16),attack_id=block[at+13])
  trace.append(dict(epoch=block[at+2],owner=names[case['owners'][row]],name=case['effects'][row]['name'],actor=actor,credit=number(at+8),reason={1:'threshold',2:'death'}[block[at+4]],impact=impact,entry_ordinal=block[at+1],time=number(at+20)))
 for i in range(block[9]):
  p=L['CARRIER_STATE_BASE']+i*L['CARRIER_WORDS'];slot,row=block[p:p+2];at=L['TARGET_COUNTER_RESOURCE_BASE']+slot*16
  if not block[p+4]&1 or block[at+3]==0 or block[at+1]!=block[p+9]:continue
  resources.append(dict(entry_ordinal=block[at+1],epoch=block[at],name=case['effects'][row]['name'],owner=case['owners'][row],actor=dict(kind=block[at+8],identity=block[at+9],generation=block[at+10]),credit=number(at+4),done=bool(block[at+2]),expires=number(at+6)))
 dead=[]
 for i in range(block[head+3]):
  at=L['TARGET_COUNTER_DEAD_BASE']+i*3;dead.append(dict(kind=block[at],identity=block[at+1],generation=block[at+2]))
 return dict(epoch=block[head+1],completions=trace,resources=resources,dead_actors=sorted(dead,key=lambda a:(a['kind'],a['identity'],a['generation'])))
def expected_native(case):
 native=observe(case);native['target_counters'].pop('events');return native
def decoded(block,meta,case,bindings):
 actual=pack.stack.decoded(block,meta,case,bindings);counter=counter_state(block,case);extra=[]
 for slot,binding in enumerate(bindings):
  gen=block[L['WORLD_ACTOR_POOL_STATE_BASE']+slot*16]
  if int(binding.kind)!=1 or gen==0:continue
  at=L['COUNTER_LANDING_EXTRA_BASE']+slot*4;amount=struct.unpack('<d',struct.pack('<II',*block[at+2:at+4]))[0];extra.append(dict(identity=binding.identity,generation=gen,extra_hits=block[at],extra_dealt=amount))
 counter['part_extra']=extra;actual['target_counters']=counter;return actual
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];base=L['TARGET_COUNTER_INPUT_BASE'];policy=base+8+2*16
 for name,at,value in [('physical-unknown-mode',base+6,2),('physical-without-native-landing',L['LANDING_META_BASE'],0),('counter-current-target-not-sentinel',L['DAMAGE_DEFINITION_BASE']+2*8,0),('counter-zero-generation',policy+3,0),('counter-zero-family',policy+6,0),('counter-miss-policy',policy+7,1),('counter-threshold-nan',policy+5,0x7ff80000),('literal-root-in-physical-mode',L['COMMAND_BASE'],43),('body-forged-as-part',base+4104,1),('unused-part-descriptor',base+4104+127*8,1)]:
  words=list(seed);words[at]=value;bad.append((name,words))
 part=next(p[0] for c,p in zip(rows,programs) if c['name']=='part-50-completion-versus-lifesteal-order')
 for name,at,value in [('part-reach-overflow',base+4104+8+1,6),('part-reserved-payload',base+4104+8+7,1)]:
  words=list(part);words[at]=value;bad.append((name,words))
 words=list(seed);step=words[2]-1;at=L['COMMAND_BASE']+step*8;words[at]=34;words[at+3:at+8]=[0,0,0,1,0];words[L['WORLD_ACTOR_LAND_INPUT_BASE']+step*2:L['WORLD_ACTOR_LAND_INPUT_BASE']+step*2+2]=[0,0x3ff00000];bad.append(('manual-pool-command-cannot-bypass-physical-impact',words))
 case=copy.deepcopy(rows[0]);case['effects'][3]['trigger']['condition']=['target_state:marker'];bad.append(('typed-child-context-not-yet-admitted',compile_case(case)[0]))
 case=copy.deepcopy(rows[0]);case['effects'].append(dict(name='unported-damage-child',source='스킬1',type='damage',stat='bonus_damage',fixed_value=100,target='boss',trigger=dict(timing=['event:target_counter_complete:marker'],condition=[])));case['owners'].append(0);bad.append(('typed-damage-child-not-yet-admitted',compile_case(case)[0]))
 return rows,programs,bad
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();native=[expected_native(c) for c in rows]
 if a.cpu_only:print('Full physical native',len(rows),'raw',len(bad),'GPU0');return
 old=json.loads((ROOT/'research/portable-world-target-counter-metal.json').read_text());oldpath=Path(old['captured']);oldin=(oldpath/'input.bin').read_bytes();oldout=(oldpath/'readback.bin').read_bytes();oldn=int.from_bytes(oldin[:4],'little');assert oldn==622;iw=97464*4;ow=524288*4
 packed=array.array('I',[len(rows)+len(bad)+oldn])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(oldn):
  w=list(struct.unpack_from('<'+'I'*97464,oldin,4+i*iw));w[0]=L['COUNTER_LANDING_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-counter-landing-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,97464,524288,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 checked=[]
 for i,(case,(_,meta,bindings),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*524288:(i+1)*524288]
  try:actual=decoded(block,meta,case,bindings);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
  except Exception as error:actual=dict(error=repr(error));changed=['decode']
  checked.append(dict(name=case['name'],passed=block[0]==0 and not changed,status=block[0],changed=changed,actual=actual,native=expected))
 rejected=[dict(name=name,status=values[(len(rows)+j)*524288],passed=values[(len(rows)+j)*524288]==64) for j,(name,_) in enumerate(bad)];offset=len(rows)+len(bad)
 preserved=[dict(index=i,passed=raw[(offset+i)*ow:(offset+i+1)*ow]==oldout[i*ow:(i+1)*ow]) for i in range(oldn)]
 report=dict(passed=all(r['passed'] for r in checked+rejected+preserved),cases=checked,rejected_cases=rejected,preserved622=preserved,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,typed_target_child_conditions=False,typed_damage_children=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-counter-landing-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[r.get('name',r.get('index')) for r in checked+rejected+preserved if not r['passed']];print('Full physical native',len(rows),'raw',len(bad),'old622 all words exact',a.backend)
if __name__=='__main__':main()
