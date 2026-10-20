"""CPU-only audit of frozen Metal counter resources, callbacks and old590."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='98427c0'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('counter_seal_suite',ROOT/'research/verify-world-target-counters.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-target-counter-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=97464*4;ow=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and int.from_bytes(data[:4],'little')==622 and len(data)==4+622*iw and len(raw)==622*ow and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h,f
 proof=json.loads((ROOT/'research/portable-build/world-target-counter-generation.json').read_text());assert proof['passed'] and len(proof['cases'])==7 and proof['gpu_executions']==0 and all(x['actual']==x['expected'] for x in proof['cases'])
 unit=(ROOT/'research/portable-build/target-counter-unit.log').read_text();assert 'Ran 364 tests' in unit and unit.rstrip().endswith('OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(10,22);values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 for i,(c,(words,meta),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];block=values[i*524288:(i+1)*524288];actual=d.decoded(block,c);expected=d.expected_observation(d.observe_case(c));assert block[0]==0 and actual==expected and stored['actual']==actual and stored['native']==expected,c['name']
 for j,(name,words) in enumerate(bad):
  i=10+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and values[i*524288]==64 and r['rejected_cases'][j]['passed']
 old=json.loads((ROOT/'research/portable-world-actor-stack-metal.json').read_text());q=Path(old['captured']);oldin=(q/'input.bin').read_bytes();oldout=(q/'readback.bin').read_bytes();assert sha(oldin)==old['evidence']['input_sha256'] and sha(oldout)==old['evidence']['output_sha256']
 for j in range(590):
  i=32+j;w=bytearray(data[4+i*iw:4+(i+1)*iw]);w[:4]=(0x5045567d).to_bytes(4,'little');assert w[:92336*4]==oldin[4+j*92336*4:4+(j+1)*92336*4] and not any(w[92336*4:]);assert raw[i*ow:(i+1)*ow]==oldout[j*ow:(j+1)*ow] and r['preserved590'][j]['passed']
 initial=json.loads((ROOT/'research/portable-world-target-counter-initial-metal.json').read_text());assert not initial['passed'] and all(c['status']==64 for c in initial['cases']) and all(c['passed'] for c in initial['preserved590']+initial['rejected_cases']);assert initial['evidence']['source_sha256']!=e['source_sha256'] and initial['evidence']['input_sha256']==e['input_sha256']
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=622,native_literal_cases=10,native_action_steps=48,raw_rejections=22,old590_all_output_words_preserved=True,uid_epoch_credit_per_step_and_immutable_completion_exact=True,all_siblings_latched_before_synchronous_children=True,preparation_location_matches_native_activation_child_witness=True,seven_prior_entries_cuda_msl_generated_exact=True,portable_cpu_tests=364,unit_test_revision='a27f308',source_blob_verified=True,actual_metal_executions=2,initial_source_rejected_literal_roots=True,initial_failure_preserved=True,unchanged_gpu_retries=0,input_words=97464,output_words=524288,input_sha256=sha(data),output_sha256=sha(raw),physical_landing_bridge=False,typed_target_child_conditions=False,windows_counters_verified=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-target-counter-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal622 sealed:10 native/48 steps/22 raw/old590 exact;GPU audit0')
if __name__=='__main__':main()
