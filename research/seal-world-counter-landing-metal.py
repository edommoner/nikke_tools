"""CPU-only audit of physical Actor counter Metal663 and retained outputs."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='e758630'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('physical_counter_seal',ROOT/'research/verify-world-counter-landings.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-counter-landing-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=97464*4;ow=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and int.from_bytes(data[:4],'little')==663 and len(data)==4+663*iw and len(raw)==663*ow and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h,f
 proof=json.loads((ROOT/'research/portable-build/world-counter-landing-generation.json').read_text());assert proof['passed'] and len(proof['cases'])==8 and proof['gpu_executions']==0 and all(x['actual']==x['expected'] for x in proof['cases'])
 for c in proof['cases']:
  for f,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 unit=(ROOT/'research/portable-build/counter-landing-repair-unit.log').read_text();assert 'Ran 369 tests' in unit and unit.rstrip().endswith('OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(26,15);values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];block=values[i*524288:(i+1)*524288];actual=d.decoded(block,meta,case,bindings);native=d.expected_native(case)
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and stored['actual']==actual and stored['native']==json.loads(json.dumps(native)),case['name']
 for j,(name,words) in enumerate(bad):
  i=26+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and values[i*524288]==64 and r['rejected_cases'][j]['passed']
 old=json.loads((ROOT/'research/portable-world-target-counter-metal.json').read_text());q=Path(old['captured']);oldin=(q/'input.bin').read_bytes();oldout=(q/'readback.bin').read_bytes();assert sha(oldin)==old['evidence']['input_sha256'] and sha(oldout)==old['evidence']['output_sha256']
 for j in range(622):
  i=41+j;w=bytearray(data[4+i*iw:4+(i+1)*iw]);w[:4]=(0x5045567e).to_bytes(4,'little');assert w==oldin[4+j*iw:4+(j+1)*iw] and raw[i*ow:(i+1)*ow]==oldout[j*ow:(j+1)*ow] and r['preserved622'][j]['passed']
 first=json.loads((ROOT/'research/portable-world-counter-landing-initial-metal.json').read_text());second=json.loads((ROOT/'research/portable-world-counter-landing-part-accounting-metal.json').read_text());assert not first['passed'] and all(c['status']==64 for c in first['cases']) and sum(c['passed'] for c in second['cases'])==21
 assert all(c['passed'] for c in first['preserved622']+second['preserved622']);assert first['evidence']['source_sha256']!=second['evidence']['source_sha256']!=e['source_sha256']
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=663,full_native_battles=26,raw_rejections=15,old622_all_output_words_preserved=True,old8_cuda_msl_generated_exact=True,portable_cpu_tests=369,physical_body_part_add_impact_before_lifesteal=True,exact_actor_receipt_preserved_through_death=True,parts_direct_and_extra_accounting_separate=True,extra_counters_reset_per_generation=True,body_plus127_parts_verified=True,physical_skill_mode_credit_family='WEAPON',shared_counter_collect_latch_and_event58=True,output_words=524288,input_words=97464,actual_metal_executions=3,unchanged_gpu_retries=0,failed_readbacks_preserved=True,input_sha256=sha(data),output_sha256=sha(raw),typed_target_child_conditions=False,typed_damage_children=False,windows_physical_counters_verified=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-counter-landing-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal663 sealed:26 full native/15 raw/old622 exact;CPU369;GPU audit0')
if __name__=='__main__':main()
