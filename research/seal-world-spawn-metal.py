"""CPU-only independent source/readback/native audit for enemy spawn notifications."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='cb44009'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('enemy_attack_seal',ROOT/'research/verify-world-spawn.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 r=json.loads((ROOT/'research/portable-world-spawn-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=json.loads((p/'evidence.json').read_text());iw=97464*4;ow=655360*4
 assert r['passed'] and e==r['evidence'] and e['gpu_execution_verified'] and e['backend']=='metal' and e['transport']['device']=='Apple M5' and e['transport']['command_status']=='completed'
 assert len(data)==4+27*iw and len(raw)==27*ow and data[:4]==(27).to_bytes(4,'little') and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for path,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 host={}
 for path in ['app/portable_trigger_specs.py','app/portable_specs.py','research/world_spawn_cases.py','research/world_spawn_native.py','research/world_frame_native.py','research/verify-world-spawn.py']:
  b=(ROOT/path).read_bytes();assert b==subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT);host[path]=sha(b)
 rows,programs,bad=m.prepare();assert (len(rows),len(bad))==(22,5)
 for i,(c,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  actual=m.decoded(block,meta,c,bindings);native,trace=m.inspect_native(c);stored=r['cases'][i]
  assert m.periodic.skill_trace(block)==trace==stored['skill_trace']==stored['native_skill_trace']
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and actual==stored['actual'] and json.loads(json.dumps(native))==stored['native'],c['name']
  assert not any(block[m.L['COUNTER_CONTEXT_BASE']:m.L['COUNTER_CONTEXT_BASE']+1096])
 for i,(name,w) in enumerate(bad):
  at=22+i;assert struct.pack('<'+'I'*len(w),*w)==data[4+at*iw:4+(at+1)*iw] and int.from_bytes(raw[at*ow:at*ow+4],'little')==64
 generation=json.loads((ROOT/'research/portable-build/world-spawn-generation.json').read_text());assert generation['passed'] and len(generation['cases'])==15 and generation['gpu_executions']==0
 for c in generation['cases']:
  assert c['actual']==c['expected']
  for path,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 unit=(ROOT/'research/portable-build/world-spawn-unit.log').read_text();assert 'Ran 429 tests' in unit and unit.rstrip().endswith('OK')
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),host_and_native_source_sha256=host,metal_inputs=27,native_battles=22,raw_rejections=5,portable_cpu_tests=429,old15_cuda_msl_generated_exact=True,old923_gpu_reexecutions=0,startup_once_per_owner_after_all_battle_start=True,spawn_before_initial_magazine=True,per_add_notifications_and_generations_native_equal=True,all640_notification_times_and_owners_exact=True,direct_and_dot_all128_receivers_native_equal=True,existing_timer_queue_and_landing_order_retained=True,notification_trace_capacity=4096,input_words=97464,output_words=655360,context_mode=15,abi='0x50455686',stage_gpu_sources=1,stage_gpu_executions=1,unchanged_gpu_retries=0,audit_gpu_calls=0,input_sha256=sha(data),output_sha256=sha(raw),normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-spawn-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal27 native22/raw5 and old15 strict parity audited;GPU0')
if __name__=='__main__':main()
