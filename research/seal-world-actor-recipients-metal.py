"""Audit frozen persistent recipient sets from actual Metal readback and native."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='e7585b8'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('recipient_seal',ROOT/'research/verify-world-actor-recipients.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d);L=d.L
 r=json.loads((ROOT/'research/portable-world-actor-recipient-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=92336*4;ow=524288*4;oldow=262144*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and int.from_bytes(data[:4],'little')==484 and len(data)==4+484*iw and len(raw)==484*ow and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 proof=json.loads((p/'world-actor-recipient-generation.json').read_text());assert proof['passed'] and len(proof['cases'])==4 and proof['gpu_executions']==0 and all(x['actual']==x['expected'] for x in proof['cases'])
 for c in proof['cases']:
  expected={k:v for k,v in e['source_sha256'].items() if k!=d.SOURCE};entry=dict(fields='gpu/world_actor_fields_entry.slang',state='gpu/world_actor_state_entry.slang',mutation='gpu/world_actor_mutation_entry.slang').get(c['name'])
  if entry:expected[entry]=sha(subprocess.check_output(['git','show',SOURCE+':'+entry],cwd=ROOT))
  assert c['source_sha256']==expected
 log=(p/'world-actor-recipient-unit.log').read_bytes();assert b'Ran 340 tests' in log and log.rstrip().endswith(b'OK')
 device=json.loads((p/'world-actor-recipients-device.json').read_text());assert device['name']=='Apple M5' and device['gpu_dispatches']==0 and len(raw)<=device['max_buffer_length'] and device['bytes_per_case']==ow
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(19,4);v=array.array('I');v.frombytes(raw)
 if sys.byteorder!='little':v.byteswap()
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];block=v[i*524288:(i+1)*524288];actual=d.decoded(block,meta,case,bindings);native=d.state.fields.pool.observe(case)
  assert stored['passed'] and stored['actual']==json.loads(json.dumps(actual)) and stored['native']==json.loads(json.dumps(native)) and all(actual[k]==native[k] for k in native if k!='scope'),case['name']
  for row in range(512):
   at=L['WORLD_ACTOR_RECIPIENT_BASE']+16+row*168;kind,count=block[at:at+2];assert kind<=2 and count<=128 and block[at+6]==block[at+7]==0
   if kind==0:assert not any(block[at:at+168]);continue
   assert count==1 if kind==1 else count>0
   order=[(block[at+136+j//4]>>((j%4)*8))&255 for j in range(count)];assert len(set(order))==len(order) and all(x<len(bindings) for x in order)
   for target in range(128):assert bool(block[at+8+target])==(target in order) and (not block[at+2+target//32]&(1<<(target%32)) or target in order)
  assert not any(block[L['WORLD_ACTOR_WIDE_IMMUNITY_BASE']:])
 for j,(name,words) in enumerate(bad):
  i=19+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and v[i*524288]==64 and r['rejected_cases'][j]['passed']
 prior=json.loads((ROOT/'research/portable-world-actor-mutation-metal.json').read_text());op=Path(prior['captured']);before=(op/'readback.bin').read_bytes();beforein=(op/'input.bin').read_bytes();assert sha(before)==prior['evidence']['output_sha256'] and sha(beforein)==prior['evidence']['input_sha256']
 for j in range(461):
  i=23+j;now=raw[i*ow:(i+1)*ow];assert now[:oldow]==before[j*oldow:(j+1)*oldow] and not any(now[oldow:]) and r['preserved461'][j]['passed'];w=bytearray(data[4+i*iw:4+(i+1)*iw]);w[:4]=(0x5045567a).to_bytes(4,'little');assert w==beforein[4+j*iw:4+(j+1)*iw]
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=484,full_native_battles=19,raw_rejections=4,old461_legacy_output_words_preserved=True,old461_new_region_zero=True,normal_fields_state_mutation_cuda_msl_generated_exact=True,portable_cpu_tests=340,source_blob_verified=True,actual_gpu_executions=1,unchanged_gpu_retries=0,max_shared_recipient_count=128,max_resident_carriers=512,output_words=524288,device_limits_measured=True,input_sha256=sha(data),output_sha256=sha(raw),windows_recipients_verified=False,wide_immunity_not_connected_yet=True,canonical_world_admission=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-actor-recipient-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal484 sealed:native19/raw4/old461 whole prefixes+zero tail;shared sets1/65/128;CPU340;GPU retry0')
if __name__=='__main__':main()
