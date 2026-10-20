"""Audit the saved Metal721 words against frozen source and full native battles."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='6348577'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('context_seal','research/verify-world-counter-context.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-counter-context-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=97464*4;ow=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and int.from_bytes(data[:4],'little')==721 and len(data)==4+721*iw and len(raw)==721*ow and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h,f
 proof=json.loads((ROOT/'research/portable-build/world-counter-context-generation.json').read_text());assert proof['passed'] and len(proof['cases'])==9 and proof['gpu_executions']==0
 for c in proof['cases']:
  assert c['actual']==c['expected']
  for f,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 unit=(ROOT/'research/portable-build/counter-context-repair-unit.log').read_text();assert 'Ran 374 tests' in unit and unit.rstrip().endswith('OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(49,9);values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];block=values[i*524288:(i+1)*524288];actual=d.physical.decoded(block,meta,case,bindings);native=d.physical.expected_native(case)
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and stored['actual']==actual and stored['native']==json.loads(json.dumps(native)),case['name']
  assert not any(block[d.L['COUNTER_CONTEXT_BASE']:d.L['COUNTER_CONTEXT_BASE']+1096]) and stored['context_restored']
 for j,(name,words) in enumerate(bad):
  i=49+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and values[i*524288]==64 and r['rejected_cases'][j]['passed']
 old=json.loads((ROOT/'research/portable-world-counter-landing-metal.json').read_text());q=Path(old['captured']);before=(q/'input.bin').read_bytes();prior=(q/'readback.bin').read_bytes();assert sha(before)==old['evidence']['input_sha256'] and sha(prior)==old['evidence']['output_sha256']
 for j in range(663):
  i=58+j;w=bytearray(data[4+i*iw:4+(i+1)*iw]);w[:4]=(0x5045567f).to_bytes(4,'little');assert w==before[4+j*iw:4+(j+1)*iw] and raw[i*ow:(i+1)*ow]==prior[j*ow:(j+1)*ow] and r['preserved663'][j]['passed']
 initial=json.loads((ROOT/'research/portable-world-counter-context-initial-metal.json').read_text());assert not initial['passed'] and all(c['passed'] for c in initial['cases']+initial['rejected_cases']) and [x['index'] for x in initial['preserved663'] if not x['passed']]==[26]
 assert initial['evidence']['source_sha256']!=e['source_sha256']
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=721,full_native_battles=49,raw_rejections=9,old663_all_output_words_preserved=True,old9_cuda_msl_generated_exact=True,portable_cpu_tests=374,immutable_completion_actor_context=True,death_without_impact_actor_retained=True,generic_named_child_clears_context=True,finite_latch_and_permanent_recheck=True,context_stack_fully_restored=True,context_mode=3,old_mode2_still_rejected=True,output_words=524288,input_words=97464,actual_metal_executions=2,unchanged_gpu_retries=0,failed_readbacks_preserved=True,input_sha256=sha(data),output_sha256=sha(raw),typed_target_child_conditions=True,typed_damage_children=False,windows_context_verified=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-counter-context-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal721 sealed:49 full native/9 raw/old663 exact;CPU374;GPU audit0')
if __name__=='__main__':main()
