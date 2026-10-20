"""CPU audit of typed enemy fields from frozen source/readback/native references."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='c2425e5'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads((ROOT/'research'/p).read_text())
def main():
 spec=importlib.util.spec_from_file_location('fields_seal',ROOT/'research/verify-world-actor-fields.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);L=d.L
 r=load('portable-world-actor-fields-metal.json');initial=load('portable-world-actor-fields-initial-metal.json');finding=load('portable-world-actor-fields-tail-verifier-finding.json');p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();iw=92208*4;ow=262144*4;e=r['evidence']
 assert r['passed'] and r['gpu_readback_reused'] and e['backend']=='metal' and e['gpu_execution_verified'];assert int.from_bytes(data[:4],'little')==357 and len(data)==4+357*iw and len(raw)==357*ow;assert sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 assert initial['captured']==r['captured'] and initial['evidence']==e and initial['cases']==r['cases'] and initial['rejected_cases']==r['rejected_cases'] and finding['gpu_retries']==0 and finding['all285_legacy_prefixes_exact']
 for name,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+name],cwd=ROOT))==h
 normal=json.loads((p/'world-actor-fields-default-parity.json').read_text());assert normal['passed'] and normal['actual']==normal['expected'];assert normal['source_sha256']=={k:v for k,v in e['source_sha256'].items() if k!=d.SOURCE}
 log=(p/'world-actor-fields-unit.log').read_bytes();assert b'Ran 314 tests' in log and log.rstrip().endswith(b'OK')
 final_log=(p/'world-actor-fields-unit-final.log').read_bytes();assert b'Ran 315 tests' in final_log and final_log.rstrip().endswith(b'OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(52,20);values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 fingerprints=[]
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];block=values[i*262144:(i+1)*262144];actual=d.decoded(block,meta,case,bindings);native=d.pool.observe(case)
  assert stored['passed'] and block[0]==0 and stored['actual']==json.loads(json.dumps(actual)) and stored['native']==json.loads(json.dumps(native)) and all(actual[k]==native[k] for k in native if k!='scope'),case['name']
 for j,((name,words),stored) in enumerate(zip(bad,r['rejected_cases'])):
  i=52+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and values[i*262144]==64 and stored['passed'] and stored['name']==name
 old=load('portable-world-actor-pools-metal.json');oldp=Path(old['captured']);before=(oldp/'readback.bin').read_bytes();before_in=(oldp/'input.bin').read_bytes();assert sha(before)==old['evidence']['output_sha256'] and sha(before_in)==old['evidence']['input_sha256'];oldow=253952*4
 for j,stored in enumerate(r['preserved285']):
  i=72+j;prior=before[j*oldow:(j+1)*oldow];now=raw[i*ow:(i+1)*ow];assert now[:oldow]==prior and stored['passed'];required=0x57463031 if int.from_bytes(prior[225280*4:225281*4],'little')==0x57485031 else 0;assert int.from_bytes(now[oldow:oldow+4],'little')==required and not any(now[oldow+4:])
  newinput=bytearray(data[4+i*iw:4+(i+1)*iw]);newinput[:4]=(0x50455677).to_bytes(4,'little');assert newinput==before_in[4+j*iw:4+(j+1)*iw]
 for i in range(357):fingerprints.append(dict(index=i,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(raw[i*ow:(i+1)*ow])))
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=357,full_native_battles=52,raw_rejections=20,old285_every_legacy_output_word_preserved=True,normal_cuda_msl_generated_exact=True,portable_cpu_tests=315,portable_cpu_tests_before_gpu=314,source_blob_verified=True,actual_gpu_executions=1,gpu_retries=0,verifier_only_tail_finding_preserved=True,native_query_and_carrier_order_exact=True,max_actor_slots=128,max_resident_carriers=512,input_sha256=sha(data),output_sha256=sha(raw),windows_fields_verified=False,canonical_world_admission=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-actor-fields-validation.json').write_text(json.dumps(result,indent=2)+'\n');(ROOT/'research/portable-world-actor-fields-fingerprints.json').write_text(json.dumps(dict(source_sha256=e['source_sha256'],cases=fingerprints),indent=2)+'\n');print('Metal357 sealed: native52/raw20/old285 all bytes;CPU315;GPU retries0')
if __name__=='__main__':main()
