"""CPU proof audit of typed named removal;no GPU functions are invoked."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='af7aae6'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('mutation_seal',ROOT/'research/verify-world-actor-mutation.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-actor-mutation-metal.json').read_text());p=Path(r['captured']);e=r['evidence'];data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();iw=92336*4;ow=262144*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and int.from_bytes(data[:4],'little')==461 and len(data)==4+461*iw and len(raw)==461*ow and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 generation=json.loads((p/'world-actor-mutation-generation.json').read_text());assert generation['passed'] and generation['gpu_executions']==0 and generation['normalization_unchanged']
 for case in generation['cases']:
  assert case['actual']==case['expected'];expected={k:v for k,v in e['source_sha256'].items() if k!=d.SOURCE};entry={'fields':'gpu/world_actor_fields_entry.slang','state':'gpu/world_actor_state_entry.slang'}.get(case['name'])
  if entry:expected[entry]=sha(subprocess.check_output(['git','show',SOURCE+':'+entry],cwd=ROOT))
  assert case['source_sha256']==expected
 for filename in ('world-actor-mutation-unit.log','world-actor-mutation-unit-fixed.log'):
  log=(p/filename).read_bytes();assert b'Ran 332 tests' in log and log.rstrip().endswith(b'OK')
 initial=json.loads((ROOT/'research/portable-world-actor-mutation-initial-metal.json').read_text());ip=Path(initial['captured']);assert not initial['passed'] and [c['name'] for c in initial['cases'] if not c['passed']]==['target-spawn-before-new-generation-drop']
 assert (ip/'input.bin').read_bytes()==data and all(c['passed'] for c in initial['rejected_cases']+initial['preserved424'])
 assert sha((ip/'readback.bin').read_bytes())==initial['evidence']['output_sha256']
 assert [f for f,h in e['source_sha256'].items() if h!=initial['evidence']['source_sha256'][f]]==['gpu/world_actor_mutation.slang']
 finding=json.loads((ROOT/'research/portable-world-actor-mutation-generation-finding.json').read_text());assert finding['overlapping_stale_carriers_rejected']==45 and finding['gpu_reexecutions']==0
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(30,7);v=array.array('I');v.frombytes(raw)
 if sys.byteorder!='little':v.byteswap()
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];actual=d.state.decoded(v[i*262144:(i+1)*262144],meta,case,bindings);native=d.state.fields.pool.observe(case)
  assert stored['passed'] and stored['actual']==json.loads(json.dumps(actual)) and stored['native']==json.loads(json.dumps(native)) and all(actual[k]==native[k] for k in native if k!='scope'),case['name']
 for j,(name,words) in enumerate(bad):
  i=30+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and v[i*262144]==64 and r['rejected_cases'][j]['passed']
 prior=json.loads((ROOT/'research/portable-world-actor-state-metal.json').read_text());op=Path(prior['captured']);before=(op/'readback.bin').read_bytes();beforein=(op/'input.bin').read_bytes();assert sha(before)==prior['evidence']['output_sha256'] and sha(beforein)==prior['evidence']['input_sha256']
 for j in range(424):
  i=37+j;assert raw[i*ow:(i+1)*ow]==before[j*ow:(j+1)*ow] and r['preserved424'][j]['passed'];w=bytearray(data[4+i*iw:4+(i+1)*iw]);w[:4]=(0x50455679).to_bytes(4,'little');assert w==beforein[4+j*iw:4+(j+1)*iw]
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=461,full_native_battles=30,raw_rejections=7,old424_every_input_and_output_word_preserved=True,normal_fields_state_cuda_msl_generated_exact=True,portable_cpu_tests=332,source_blob_verified=True,physical_gpu_executions=2,final_fixed_gpu_executions=1,unchanged_gpu_retries=0,initial_generation_failure_preserved=True,typed_scope_snapshotted_once=True,all_retirement_before_callbacks=True,max_actor_slots=128,max_resident_carriers=512,input_sha256=sha(data),output_sha256=sha(raw),windows_mutation_verified=False,canonical_world_admission=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-actor-mutation-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal461 sealed:native30/raw7/old424 whole outputs;CPU332;GPU retries0')
if __name__=='__main__':main()
