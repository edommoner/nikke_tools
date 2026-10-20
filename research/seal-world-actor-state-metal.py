"""CPU audit of both physical Metal runs and composed typed named-state proof."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='8c5a09b'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name):return json.loads((ROOT/'research'/name).read_text())
def main():
 spec=importlib.util.spec_from_file_location('state_seal',ROOT/'research/verify-world-actor-state.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
 r=load('portable-world-actor-state-metal.json');initial=load('portable-world-actor-state-initial-metal.json');p=Path(r['captured']);prior=Path(initial['captured']);e=r['evidence'];data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();oldinput=(prior/'input.bin').read_bytes();oldoutput=(prior/'readback.bin').read_bytes();ie=initial['evidence'];fresh=(p/'dispatch-readback.bin').read_bytes();freshinput=(p/'dispatch-input.bin').read_bytes();fe=json.loads((p/'dispatch-evidence.json').read_text());iw=92336*4;ow=262144*4
 assert r['passed'] and not initial['passed'] and initial['cases'][37]['changed']==['decode']
 assert all(x['passed'] for i,x in enumerate(initial['cases']) if i!=37) and all(x['passed'] for x in initial['rejected_cases']+initial['preserved357'])
 assert int.from_bytes(data[:4],'little')==424 and len(data)==4+424*iw and len(raw)==424*ow and len(fresh)==ow and len(freshinput)==4+iw
 for inp,out,ev in [(data,raw,e),(oldinput,oldoutput,ie),(freshinput,fresh,fe)]:assert sha(inp)==ev['input_sha256'] and sha(out)==ev['output_sha256'] and ev['gpu_execution_verified'] and ev['backend']=='metal'
 assert e['source_sha256']==ie['source_sha256']==fe['source_sha256'] and e['generated_sha256']==ie['generated_sha256']==fe['generated_sha256']
 assert e['execution_composition']['changed_indices']==[37] and e['transport']['fresh_inputs']==1 and e['transport']['reused_inputs']==423
 assert freshinput[:4]==(1).to_bytes(4,'little') and freshinput[4:]==data[4+37*iw:4+38*iw] and raw[37*ow:38*ow]==fresh
 for i in range(424):
  if i==37:assert data[4+i*iw:4+(i+1)*iw]!=oldinput[4+i*iw:4+(i+1)*iw]
  else:assert data[4+i*iw:4+(i+1)*iw]==oldinput[4+i*iw:4+(i+1)*iw] and raw[i*ow:(i+1)*ow]==oldoutput[i*ow:(i+1)*ow]
 for name,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+name],cwd=ROOT))==h
 for name,entry in [('default',None),('prior-fields','gpu/world_actor_fields_entry.slang')]:
  proof=json.loads((p/('world-actor-state-'+name+'-parity.json')).read_text());assert proof['passed'] and proof['actual']==proof['expected'];expected={k:v for k,v in e['source_sha256'].items() if k!=d.SOURCE}
  if entry:expected[entry]=sha(subprocess.check_output(['git','show',SOURCE+':'+entry],cwd=ROOT))
  assert proof['source_sha256']==expected
 for file,count in [('world-actor-state-unit.log',323),('world-actor-state-unit-fixed.log',324)]:
  log=(p/file).read_bytes();assert ('Ran %d tests'%count).encode() in log and log.rstrip().endswith(b'OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(49,18);v=array.array('I');v.frombytes(raw)
 if sys.byteorder!='little':v.byteswap()
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];actual=d.decoded(v[i*262144:(i+1)*262144],meta,case,bindings);native=d.fields.pool.observe(case)
  assert stored['passed'] and stored['actual']==json.loads(json.dumps(actual)) and stored['native']==json.loads(json.dumps(native)) and all(actual[k]==native[k] for k in native if k!='scope'),case['name']
 for j,(name,words) in enumerate(bad):
  i=49+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and v[i*262144]==64 and r['rejected_cases'][j]['passed']
 old=load('portable-world-actor-fields-metal.json');op=Path(old['captured']);before=(op/'readback.bin').read_bytes();beforein=(op/'input.bin').read_bytes();assert sha(before)==old['evidence']['output_sha256'] and sha(beforein)==old['evidence']['input_sha256']
 for j in range(357):
  i=67+j;assert raw[i*ow:(i+1)*ow]==before[j*ow:(j+1)*ow];newinput=bytearray(data[4+i*iw:4+(i+1)*iw]);newinput[:4]=(0x50455678).to_bytes(4,'little');assert newinput[:-512]==beforein[4+j*92208*4:4+(j+1)*92208*4] and not any(newinput[-512:])
 oldnative=load('portable-world-actor-state-old-native-parity.json');assert oldnative['passed'] and oldnative['old_native_dictionaries']==125 and all(x['passed'] for x in oldnative['checks']) and oldnative['gpu_executions']==0
 result=dict(passed=True,old125_native_dictionaries_preserved=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=424,full_native_battles=49,raw_rejections=18,old357_every_output_word_preserved=True,normal_cuda_msl_generated_exact=True,prior_fields_cuda_msl_generated_exact=True,portable_cpu_tests=324,portable_cpu_tests_before_first_gpu=323,source_blob_verified=True,physical_gpu_executions=2,initial_inputs=424,changed_literal_input_execution=1,reused_identical_input_blocks=423,unchanged_gpu_retries=0,initial_packing_failure_preserved=True,native_runtime_health_finding_open=True,input_sha256=sha(data),output_sha256=sha(raw),windows_state_verified=False,canonical_world_admission=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-actor-state-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal424 sealed:native49/raw18/old357 bytes;fresh corrected1,reused423;CPU324;GPU unchanged retries0')
if __name__=='__main__':main()
