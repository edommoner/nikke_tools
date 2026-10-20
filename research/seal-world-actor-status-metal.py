"""CPU audit:typed128 status loop,new pools,and previous484 exact readbacks."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='0873bd9'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('status_seal',ROOT/'research/verify-world-actor-status.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-actor-status-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=92336*4;ow=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and int.from_bytes(data[:4],'little')==529 and len(data)==4+529*iw and len(raw)==529*ow and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 proof=json.loads((p/'world-actor-status-generation.json').read_text());assert proof['passed'] and len(proof['cases'])==5 and proof['gpu_executions']==0 and all(x['actual']==x['expected'] for x in proof['cases'])
 entries=dict(fields='gpu/world_actor_fields_entry.slang',state='gpu/world_actor_state_entry.slang',mutation='gpu/world_actor_mutation_entry.slang',recipient='gpu/world_actor_recipient_entry.slang')
 for c in proof['cases']:
  expected={k:v for k,v in e['source_sha256'].items() if k!=d.SOURCE};entry=entries.get(c['name'])
  if entry:expected[entry]=sha(subprocess.check_output(['git','show',SOURCE+':'+entry],cwd=ROOT))
  assert c['source_sha256']==expected
 log=(p/'world-actor-status-unit-final.log').read_bytes();assert b'Ran 348 tests' in log and log.rstrip().endswith(b'OK')
 device=json.loads((p/'world-actor-recipients-device.json').read_text());assert device['name']=='Apple M5' and device['gpu_dispatches']==0 and len(raw)<=device['max_buffer_length']
 initial=json.loads((p/'world-actor-status-generation-initial.json').read_text());finding=json.loads((ROOT/'research/portable-world-actor-status-generation-layout-finding.json').read_text());assert not initial['passed'] and finding['gpu_dispatches_before_fix']==0 and finding['normalizer_unchanged']
 generation=json.loads((ROOT/'research/portable-world-actor-status-generation-contract.json').read_text());assert generation['passed'] and generation['stale_generation_charge_uses']==3 and generation['count_immunity_uses_membership_until_actual_drop'] and generation['gpu_executions']==0
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(37,8);v=array.array('I');v.frombytes(raw)
 if sys.byteorder!='little':v.byteswap()
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];block=v[i*524288:(i+1)*524288];actual=d.decoded(block,meta,case,bindings);native=d.recipient.state.fields.pool.observe(case)
  assert stored['passed'] and stored['actual']==json.loads(json.dumps(actual)) and stored['native']==json.loads(json.dumps(native)) and all(actual[k]==native[k] for k in native if k!='scope'),case['name']
 for j,(name,words) in enumerate(bad):
  i=37+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and v[i*524288]==64 and r['rejected_cases'][j]['passed']
 prior=json.loads((ROOT/'research/portable-world-actor-recipient-metal.json').read_text());op=Path(prior['captured']);before=(op/'readback.bin').read_bytes();beforein=(op/'input.bin').read_bytes();assert sha(before)==prior['evidence']['output_sha256'] and sha(beforein)==prior['evidence']['input_sha256']
 for j in range(484):
  i=45+j;assert raw[i*ow:(i+1)*ow]==before[j*ow:(j+1)*ow] and r['preserved484'][j]['passed'];w=bytearray(data[4+i*iw:4+(i+1)*iw]);w[:4]=(0x5045567b).to_bytes(4,'little');assert w==beforein[4+j*iw:4+(j+1)*iw]
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=529,full_native_battles=37,raw_rejections=8,old484_all_output_words_preserved=True,normal_fields_state_mutation_recipient_cuda_msl_generated_exact=True,portable_cpu_tests=348,source_blob_verified=True,actual_gpu_executions=1,unchanged_gpu_retries=0,ordinary_immunity_generation_aware=True,count_pools_follow_native_membership_until_drop=True,count_pools_per_actor_and_name=True,shared_cleanse_and_silent_last_recipient_retirement=True,output_words=524288,device_limits_measured=True,input_sha256=sha(data),output_sha256=sha(raw),windows_status_verified=False,canonical_world_admission=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-actor-status-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal529 sealed:native37/raw8/old484 whole outputs;CPU348;GPU retry0')
if __name__=='__main__':main()
