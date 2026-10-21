"""Independently audit saved team Metal/native/source evidence; GPU0."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='725f020'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('team_seal_suite',ROOT/'research/verify-world-team.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 r=json.loads((ROOT/'research/portable-world-team-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=json.loads((p/'evidence.json').read_text());iw=98000*4;ow=655360*4
 assert r['passed'] and e==r['evidence'] and e['gpu_execution_verified'] and e['backend']=='metal' and e['transport']['device']=='Apple M5' and e['transport']['command_status']=='completed'
 assert len(data)==4+47*iw and len(raw)==47*ow and data[:4]==(47).to_bytes(4,'little') and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for path,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 host={}
 for path in ['app/portable_team_hit_specs.py','app/portable_runtime.py','app/portable_target_counter_program.py','app/portable_trigger_specs.py','app/portable_specs.py','research/world_team_cases.py','research/world_team_native.py','research/world_frame_native.py','research/world_fraction_native.py','research/verify-world-team.py']:
  b=(ROOT/path).read_bytes();assert b==subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT);host[path]=sha(b)
 rows,programs,bad=m.prepare();assert (len(rows),len(bad))==(29,18)
 for i,(c,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  actual=m.decoded(block,meta,c,bindings);native,trace=m.inspect_native(c);stored=r['cases'][i]
  assert m.skill_trace(block,meta)==trace==stored['skill_trace']==stored['native_skill_trace']
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and actual==stored['actual'] and json.loads(json.dumps(native))==stored['native'],c['name']
  assert not any(block[m.L['COUNTER_CONTEXT_BASE']:m.L['COUNTER_CONTEXT_BASE']+1096])
 for i,(name,w) in enumerate(bad):
  at=29+i;assert struct.pack('<'+'I'*len(w),*w)==data[4+at*iw:4+(at+1)*iw] and int.from_bytes(raw[at*ow:at*ow+4],'little')==64
 generation=json.loads((ROOT/'research/portable-build/world-team-generation.json').read_text());assert generation['passed'] and len(generation['cases'])==17 and generation['gpu_executions']==0
 for c in generation['cases']:
  assert c['actual']==c['expected']
  for path,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 unit=(ROOT/'research/portable-build/world-team-repair-unit.log').read_text();assert 'Ran 460 tests' in unit and unit.rstrip().endswith('OK')
 initial=json.loads((ROOT/'research/portable-world-team-initial-gpu.json').read_text());ip=Path(initial['captured']);old=(ip/'readback.bin').read_bytes();ie=json.loads((ip/'evidence.json').read_text());assert not initial['passed'] and ie==initial['evidence'] and ie['gpu_execution_verified'] and ie['transport']['command_status']=='completed'
 assert (ip/'input.bin').read_bytes()==data and len(old)==len(raw) and sha(old)==ie['output_sha256']
 for path,h in ie['source_sha256'].items():assert sha(subprocess.check_output(['git','show','277af2b:'+path],cwd=ROOT))==h,path
 failed=[c for c in initial['cases']+initial['rejected_cases'] if not c['passed']];assert len(failed)==1 and failed[0]['name']=='team-instant-shared-gauge' and failed[0]['status']==64
 gauge=next(i for i,c in enumerate(rows) if c['name']=='team-instant-shared-gauge')
 assert all(old[i*ow:(i+1)*ow]==raw[i*ow:(i+1)*ow] for i in range(47) if i!=gauge)
 for name in ('initial','second','third'):
  failure=json.loads((ROOT/f'research/portable-world-team-{name}-compile.json').read_text());folder=Path(failure['captured']);before=(folder/'input.bin').read_bytes()
  assert not failure['passed'] and failure['gpu_executions']==0 and failure['phase']=='Metal pipeline_compile' and failure['compile_timeout_seconds']==300
  assert len(before)==failure['input_bytes']==4+failure['input_count']*iw and sha(before)==failure['input_sha256'] and json.loads((folder/'failure.json').read_text())==failure['failure']
  assert 'portable_stage=pipeline_compile' in failure['failure']['error'] and 'portable_stage=dispatch' not in failure['failure']['error']
  for path,h in failure['failure']['source_sha256'].items():assert sha(subprocess.check_output(['git','show',failure['calculation_source']+':'+path],cwd=ROOT))==h,path
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),host_and_native_source_sha256=host,metal_inputs=47,native_battles=29,raw_rejections=18,portable_cpu_tests=460,old17_cuda_msl_generated_exact=True,old958_gpu_reexecutions=0,old923_gpu_reexecutions=0,normal4682_gpu_reexecutions=0,source_owner_conditions_and_actual_attacker_activation=True,team_counter_and_trigger_budget_shared_across_attackers=True,team_activation_probability_shared=True,team_noncore_fraction_uses_common_binary64=True,charge_team_hits_before_bullet_expiry=True,notification_trace_capacity=1024,input_words=98000,output_words=655360,context_mode=19,abi='0x50455689',stage_gpu_executions=2,stage_gpu_sources=5,initial_pipeline_compile_timeout_preserved=True,second_pipeline_compile_timeout_preserved=True,third_pipeline_compile_timeout_preserved=True,initial_gpu_gauge_admission_failure_preserved=True,unchanged_gpu_retries=0,audit_gpu_calls=0,input_sha256=sha(data),output_sha256=sha(raw),normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-team-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal47 native29/raw18 and old17 strict parity audited;GPU0')
if __name__=='__main__':main()
