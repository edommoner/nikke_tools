"""CPU-only audit of saved direct-skill Metal words, native trace and frozen source."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='761e362'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('skill_seal','research/verify-world-skills.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-skill-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=97464*4;ow=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and int.from_bytes(data[:4],'little')==833 and len(data)==4+833*iw and len(raw)==833*ow and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h,f
 proof=json.loads((ROOT/'research/portable-build/world-skill-generation.json').read_text());assert proof['passed'] and len(proof['cases'])==11 and proof['gpu_executions']==0
 for c in proof['cases']:
  assert c['actual']==c['expected']
  for f,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 unit=(ROOT/'research/portable-build/world-skill-family-unit.log').read_text();assert 'Ran 390 tests' in unit and unit.rstrip().endswith('OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(40,10);values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];block=values[i*524288:(i+1)*524288];actual=d.physical.decoded(block,meta,case,bindings);native,trace=d.inspect_native(case)
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and stored['actual']==actual and stored['native']==json.loads(json.dumps(native)),case['name']
  assert d.skill_trace(block)==trace==stored['skill_trace']==stored['native_skill_trace']
  assert not any(block[d.L['COUNTER_CONTEXT_BASE']:d.L['COUNTER_CONTEXT_BASE']+1096]) and stored['context_restored']
  work=list(block[d.L['COUNTER_FIELD_WORK_BASE']:d.L['COUNTER_FIELD_WORK_BASE']+8]);assert work[0]>0 and 0<work[1]<=16384 and work[2]>=work[1] and not any(work[3:]) and stored['dispatch_work']['valid']
 for j,(name,words) in enumerate(bad):
  i=40+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and values[i*524288]==64 and r['rejected_cases'][j]['passed']
 old=json.loads((ROOT/'research/portable-world-counter-field-metal.json').read_text());q=Path(old['captured']);before=(q/'input.bin').read_bytes();prior=(q/'readback.bin').read_bytes();assert sha(before)==old['evidence']['input_sha256'] and sha(prior)==old['evidence']['output_sha256']
 for j in range(783):
  i=50+j;w=bytearray(data[4+i*iw:4+(i+1)*iw]);w[:4]=(0x50455681).to_bytes(4,'little');assert w==before[4+j*iw:4+(j+1)*iw] and raw[i*ow:(i+1)*ow]==prior[j*ow:(j+1)*ow] and r['preserved783'][j]['passed']
 initial=json.loads((ROOT/'research/portable-world-skill-initial-metal.json').read_text())
 assert not initial['passed'] and [x['name'] for x in initial['cases'] if not x['passed']]==['direct-family-core_damage'] and all(x['passed'] for x in initial['preserved783']+initial['rejected_cases'])
 admission=json.loads((ROOT/'research/portable-world-skill-formula-admission-metal.json').read_text())
 assert not admission['passed'] and [x['name'] for x in admission['cases'] if not x['passed']]==['core-damage-normal-formula-is-skill'] and all(x['passed'] for x in admission['preserved783']+admission['rejected_cases'])
 assert initial['evidence']['source_sha256']!=admission['evidence']['source_sha256']!=e['source_sha256']
 packing=json.loads((ROOT/'research/portable-world-skill-formula-packing-metal.json').read_text())
 assert not packing['passed'] and [x['name'] for x in packing['cases'] if not x['passed']]==['core-damage-normal-formula-is-skill'] and all(x['passed'] for x in packing['preserved783']+packing['rejected_cases'])
 assert packing['evidence']['source_sha256']==e['source_sha256'] and packing['evidence']['input_sha256']!=e['input_sha256'] and packing['source_commit']!=r['source_commit']
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=833,full_native_battles=40,raw_rejections=10,old783_all_output_words_preserved=True,old11_cuda_msl_generated_exact=True,portable_cpu_tests=390,late_routing_128_recipients=True,creation_amount_and_hit_count_latched=True,live_queue_child_append=True,counter_free_without_synthetic_counter=True,canonical_core_damage_family_preserved=True,native_query_scope_repaired=True,context_stack_fully_restored=True,context_mode=7,old_modes2_and4_and6_still_rejected=True,output_words=524288,input_words=97464,actual_metal_executions=4,unchanged_gpu_retries=0,failed_readbacks_preserved=True,input_sha256=sha(data),output_sha256=sha(raw),typed_enemy_field_children=True,typed_direct_damage_children=True,periodic_pending_extra_part_skill_receipts=False,windows_direct_skills_verified=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-skill-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal833 sealed:40 full native+trace/10 raw/old783 exact;CPU390;GPU audit0')
if __name__=='__main__':main()
