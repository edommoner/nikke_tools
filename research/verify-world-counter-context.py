"""One typed completion-context fixture table and oracle for both GPU backends."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import world_counter_context_cases as cases
s=importlib.util.spec_from_file_location('context_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
SOURCE='gpu/counter_context_entry.slang'
def fixtures():return cases.fixtures(physical)
def compile_case(case):
 return cases.compile_case(physical,case)
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];probe=len(rows[0]['effects'])-1;condition=L['CONDITION_BASE']+probe*L['CONDITION_WORDS']
 for name,at,value in [('unknown-context-mode',L['TARGET_COUNTER_INPUT_BASE']+6,4),('context-without-native-landings',L['LANDING_META_BASE'],0),('unknown-context-condition',condition,999),('predicate-nonzero-argument',condition+3,0x3ff00000),('counter-condition-not-yet-admitted',L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F['CONDITION_COUNT'],1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 named=next(p[0] for c,p in zip(rows,programs) if c['name']=='body-completion-versus-lifesteal-order-target_state:marker')
 w=list(named);w[condition+1]=256;bad.append(('context-name-overflow',w))
 for stat,kind,value in [('bonus_damage','damage',100),('received_dmg_pct','buff',10)]:
  c=copy.deepcopy(rows[0]);c['effects'].append(dict(name='unported-context-child',source='스킬1',type=kind,stat=stat,fixed_value=value,target='boss',duration=.3,trigger=dict(timing=['event:target_counter_complete:marker'],condition=[])));c['owners'].append(0)
  bad.append(('unported-child-'+kind,compile_case(c)[0]))
 c=copy.deepcopy(rows[0]);c['effects'][-1].update(stat='max_hp_pct',duration=-1);c['effects'][-1]['trigger']['condition']=['target_state:marker'];bad.append(('unresolved-native-permanent-health-condition',compile_case(c)[0]))
 return rows,programs,bad
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args()
 rows,programs,bad=prepare();native=[physical.expected_native(c) for c in rows]
 if a.cpu_only:
  print('Full native context',len(rows),'raw',len(bad),'GPU0');return
 old=json.loads((ROOT/'research/portable-world-counter-landing-metal.json').read_text());p=Path(old['captured']);before=(p/'input.bin').read_bytes();prior=(p/'readback.bin').read_bytes();assert int.from_bytes(before[:4],'little')==663
 iw=97464*4;ow=524288*4;packed=array.array('I',[len(rows)+len(bad)+663])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(663):
  w=list(struct.unpack_from('<'+'I'*97464,before,4+i*iw));w[0]=L['COUNTER_CONTEXT_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-counter-context-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,97464,524288,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 checked=[]
 for i,(case,(_,meta,bindings),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*524288:(i+1)*524288]
  try:
   actual=physical.decoded(block,meta,case,bindings);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
   context_zero=not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096])
  except Exception as error:actual=dict(error=repr(error));changed=['decode'];context_zero=False
  checked.append(dict(name=case['name'],passed=block[0]==0 and not changed and context_zero,status=block[0],changed=changed,context_restored=context_zero,actual=actual,native=expected))
 rejected=[dict(name=name,status=values[(len(rows)+j)*524288],passed=values[(len(rows)+j)*524288]==64) for j,(name,_) in enumerate(bad)];offset=len(rows)+len(bad)
 kept=[dict(index=i,passed=raw[(offset+i)*ow:(offset+i+1)*ow]==prior[i*ow:(i+1)*ow]) for i in range(663)]
 report=dict(passed=all(r['passed'] for r in checked+rejected+kept),cases=checked,rejected_cases=rejected,preserved663=kept,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,typed_target_child_conditions=True,typed_damage_children=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-counter-context-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[r.get('name',r.get('index')) for r in checked+rejected+kept if not r['passed']];print('Context native',len(rows),'raw',len(bad),'old663 all words exact',a.backend)
if __name__=='__main__':main()
