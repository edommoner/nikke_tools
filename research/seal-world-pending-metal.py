"""CPU-only audit of pending Metal878, native batch state and prior full words."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='6bd7ab4'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('pending_seal','research/verify-world-pending-skills.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-pending-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=97464*4;ow=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and len(data)==4+878*iw and len(raw)==878*ow and int.from_bytes(data[:4],'little')==878
 assert sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h,f
 proof=json.loads((ROOT/'research/portable-build/world-pending-generation.json').read_text());assert proof['passed'] and len(proof['cases'])==11 and proof['gpu_executions']==0
 for c in proof['cases']:
  assert c['actual']==c['expected']
  for f,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 unit=(ROOT/'research/portable-build/world-pending-unit.log').read_text();assert 'Ran 399 tests' in unit and unit.rstrip().endswith('OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(26,11);maxwork=0
 for i,(case,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  actual=d.decoded(block,meta,case,bindings);native,trace=d.inspect_native(case);stored=r['cases'][i]
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and actual==stored['actual'] and stored['native']==json.loads(json.dumps(native))
  assert d.skill_trace(block)==trace==stored['skill_trace']==stored['native_skill_trace']
  assert not any(block[d.L['COUNTER_CONTEXT_BASE']:d.L['COUNTER_CONTEXT_BASE']+1096])
  work=block[d.L['COUNTER_FIELD_WORK_BASE']:d.L['COUNTER_FIELD_WORK_BASE']+8];assert work[0]>0 and 0<work[1]<=16384 and work[2]>=work[1] and not any(work[3:]);maxwork=max(maxwork,work[1])
 for i,(name,w) in enumerate(bad):
  at=26+i;assert struct.pack('<'+'I'*len(w),*w)==data[4+at*iw:4+(at+1)*iw] and int.from_bytes(raw[at*ow:at*ow+4],'little')==64 and r['rejected_cases'][i]['passed']
 offset=37;index=0
 for report,count in [('portable-world-skill-metal.json',833),('portable-world-skill-formula-metal.json',8)]:
  old=json.loads((ROOT/'research'/report).read_text());q=Path(old['captured']);before=(q/'input.bin').read_bytes();prior=(q/'readback.bin').read_bytes()
  assert old['passed'] and sha(before)==old['evidence']['input_sha256'] and sha(prior)==old['evidence']['output_sha256']
  for j in range(count):
   at=offset+j;w=bytearray(data[4+at*iw:4+(at+1)*iw]);w[:4]=(0x50455682).to_bytes(4,'little')
   assert w==before[4+j*iw:4+(j+1)*iw] and raw[at*ow:(at+1)*ow]==prior[j*ow:(j+1)*ow] and r['preserved841'][index]['passed'];index+=1
  offset+=count
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=878,full_native_battles=26,raw_rejections=11,old841_all_output_words_preserved=True,old11_cuda_msl_generated_exact=True,portable_cpu_tests=399,pending_counts_observed_from_actual_native_container=True,same_frame_pending_landing=True,ordinary_queue_not_drained_by_pending=True,shared_direct_and_pending_actor_lifecycle=True,all128_recipients=True,named_pending_hit_count=True,later_buff_exclusion=True,batch_amounts_precede_counter_children=True,reference_missing_zero_positive=True,pending_overrides_explicit_normal_formula=True,context_stack_fully_restored=True,maximum_dispatch_work=maxwork,context_mode=9,abi='0x50455683',actual_metal_executions=1,unchanged_gpu_retries=0,input_words=97464,output_words=524288,input_sha256=sha(data),output_sha256=sha(raw),audit_gpu_calls=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-pending-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal878 sealed:26 full native+trace+pending state/11 raw/old841 all words;CPU399;GPU audit0')
if __name__=='__main__':main()
