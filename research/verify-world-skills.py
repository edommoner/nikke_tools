"""One full-native late-routing skill table and oracle for both GPU backends."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import world_skill_cases as cases
from world_skill_native import inspect as inspect_native
s=importlib.util.spec_from_file_location('context_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
SOURCE='gpu/world_skill_entry.slang'
def fixtures():return cases.fixtures(physical)
def compile_case(case):
 return cases.compile_case(physical,case)
def skill_trace(block):
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 h=L['WORLD_SKILL_HEAD_BASE'];assert block[h]==0x57534b31 and block[h+1]<=128
 rows=[]
 for i in range(block[h+1]):
  at=L['WORLD_SKILL_TRACE_BASE']+i*48;n=block[at+3];assert n<=128;packed=block[at+16:at+48];recipients=[((packed[k//4]>>((k%4)*8))&255)-1 for k in range(n)]
  assert all(0<=v<128 for v in recipients) and not any((packed[k//4]>>((k%4)*8))&255 for k in range(n,128))
  bits=[0]*4
  for target in recipients:bits[target//32]|=1<<(target%32)
  assert list(block[at+12:at+16])==bits
  rows.append(dict(row=block[at],hit=block[at+1],hits=block[at+2],created=number(at+4),landed=number(at+6),amount=number(at+8),share=number(at+10),recipients=recipients))
 return rows
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];skill=next(i for i,e in enumerate(rows[0]['effects']) if e.get('type')=='damage');definition=L['DEFINITION_BASE']+skill*L['DEFINITION_WORDS'];packet=L['DAMAGE_DEFINITION_BASE']+skill*8
 for name,at,value in [('unknown-skill-mode',L['TARGET_COUNTER_INPUT_BASE']+6,8),('skill-without-native-landings',L['LANDING_META_BASE'],0),('skill-route-overflow',packet,10),('skill-recipient-zero',packet+1,0),('skill-recipient-overflow',packet+1,129),('skill-hit-overflow',packet+2,257),('skill-explicit-parts-unported',definition+F['DAMAGE_FLAGS'],65536),('skill-dot-unported',definition+F['DAMAGE_FLAGS'],128),('skill-flags-overflow',definition+F['DAMAGE_FLAGS'],0x80000000)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 w=list(seed);w[definition+F['INTERVAL']:definition+F['INTERVAL']+2]=list(struct.unpack('<II',struct.pack('<d',.1)));bad.append(('skill-periodic-unported',w))
 return rows,programs,bad
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args()
 rows,programs,bad=prepare();observed=[inspect_native(c) for c in rows];native=[r[0] for r in observed];native_traces=[r[1] for r in observed]
 if a.cpu_only:
  print('Full native world skills',len(rows),'raw',len(bad),'GPU0');return
 old=json.loads((ROOT/'research/portable-world-counter-field-metal.json').read_text());p=Path(old['captured']);before=(p/'input.bin').read_bytes();prior=(p/'readback.bin').read_bytes();assert int.from_bytes(before[:4],'little')==783
 iw=97464*4;ow=524288*4;packed=array.array('I',[len(rows)+len(bad)+783])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(783):
  w=list(struct.unpack_from('<'+'I'*97464,before,4+i*iw));w[0]=L['WORLD_SKILL_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-skill-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,97464,524288,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 checked=[]
 for i,(case,(_,meta,bindings),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*524288:(i+1)*524288]
  work=list(block[L['COUNTER_FIELD_WORK_BASE']:L['COUNTER_FIELD_WORK_BASE']+8]);work_valid=work[0]>0 and 0<work[1]<=L['CARRIERS']*L['DEPTH'] and work[2]>=work[1] and not any(work[3:])
  if case['name']=='world-skill-fanout128-holds-completion-marker':work_valid=work_valid and work[1]>4096
  try:
   actual=physical.decoded(block,meta,case,bindings);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
   trace=skill_trace(block)
   if trace!=native_traces[i]:changed.append('skill_trace')
   context_zero=not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096])
  except Exception as error:actual=dict(error=repr(error));changed=['decode'];context_zero=False;trace=[]
  checked.append(dict(name=case['name'],passed=block[0]==0 and not changed and context_zero and work_valid,status=block[0],changed=changed,context_restored=context_zero,dispatch_work=dict(count=work[0],maximum=work[1],total=work[2],guard_exits=work[3],valid=work_valid),actual=actual,native=expected,skill_trace=trace,native_skill_trace=native_traces[i]))
 rejected=[dict(name=name,status=values[(len(rows)+j)*524288],passed=values[(len(rows)+j)*524288]==64) for j,(name,_) in enumerate(bad)];offset=len(rows)+len(bad)
 kept=[dict(index=i,passed=raw[(offset+i)*ow:(offset+i+1)*ow]==prior[i*ow:(i+1)*ow]) for i in range(783)]
 report=dict(passed=all(r['passed'] for r in checked+rejected+kept),cases=checked,rejected_cases=rejected,preserved783=kept,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,typed_target_child_conditions=True,typed_enemy_field_children=True,typed_damage_children=True,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-skill-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[r.get('name',r.get('index')) for r in checked+rejected+kept if not r['passed']];print('World skill native',len(rows),'raw',len(bad),'old783 all words exact',a.backend)
if __name__=='__main__':main()
