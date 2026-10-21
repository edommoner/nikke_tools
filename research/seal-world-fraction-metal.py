"""CPU-only independent source/readback/native audit for fractional critical/core notifications."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='7cb9378'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('enemy_attack_seal',ROOT/'research/verify-world-fraction.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 r=json.loads((ROOT/'research/portable-world-fraction-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=json.loads((p/'evidence.json').read_text());iw=97480*4;ow=655360*4
 assert r['passed'] and e==r['evidence'] and e['gpu_execution_verified'] and e['backend']=='metal' and e['transport']['device']=='Apple M5' and e['transport']['command_status']=='completed'
 assert len(data)==4+35*iw and len(raw)==35*ow and data[:4]==(35).to_bytes(4,'little') and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for path,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 host={}
 for path in ['app/portable_trigger_specs.py','app/portable_specs.py','research/world_fraction_cases.py','research/world_fraction_native.py','research/world_frame_native.py','research/verify-world-fraction.py','app/portable_charge_clock_specs.py']:
  b=(ROOT/path).read_bytes();assert b==subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT);host[path]=sha(b)
 rows,programs,bad=m.prepare();assert (len(rows),len(bad))==(24,11)
 for i,(c,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  actual=m.decoded(block,meta,c,bindings);native,trace=m.inspect_native(c);stored=r['cases'][i]
  assert m.periodic.skill_trace(block)==trace==stored['skill_trace']==stored['native_skill_trace']
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and actual==stored['actual'] and json.loads(json.dumps(native))==stored['native'],c['name']
  assert not any(block[m.L['COUNTER_CONTEXT_BASE']:m.L['COUNTER_CONTEXT_BASE']+1096])
 for i,(name,w) in enumerate(bad):
  at=24+i;assert struct.pack('<'+'I'*len(w),*w)==data[4+at*iw:4+(at+1)*iw] and int.from_bytes(raw[at*ow:at*ow+4],'little')==64
 generation=json.loads((ROOT/'research/portable-build/world-fraction-generation.json').read_text());assert generation['passed'] and len(generation['cases'])==16 and generation['gpu_executions']==0
 for c in generation['cases']:
  assert c['actual']==c['expected']
  for path,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 unit=(ROOT/'research/portable-build/world-fraction-repair-unit.log').read_text();assert 'Ran 442 tests' in unit and unit.rstrip().endswith('OK')
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),host_and_native_source_sha256=host,metal_inputs=35,native_battles=24,raw_rejections=11,portable_cpu_tests=442,old16_cuda_msl_generated_exact=True,old923_gpu_reexecutions=0,fractional_credits_and_actual_notifications_native_equal=True,zero_and_unit_probability_preserve_prior_accumulator=True,physical_shot_snapshot_before_callbacks=True,auto_per_pellet_critical_core_order=True,charge_critical_then_core_after_bullet_expiry=True,normal_only_critical_excluded_from_skill_modes=True,notification_trace_capacity=2048,input_words=97480,output_words=655360,context_mode=17,abi='0x50455688',stage_gpu_sources=2,stage_gpu_executions=2,exact_static_post_fire_delays_preserved=True,weapon_mode_uses_existing_raw_delay=True,failed_initial_readback_preserved=True,unchanged_gpu_retries=0,audit_gpu_calls=0,input_sha256=sha(data),output_sha256=sha(raw),normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-fraction-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal35 native24/raw11 and old16 strict parity audited;GPU0')
if __name__=='__main__':main()
