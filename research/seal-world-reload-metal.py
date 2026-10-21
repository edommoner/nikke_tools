"""Independent saved readback/native/source audit of common reload behavior;GPU0."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='76344c0'
def sha(b):return hashlib.sha256(b).hexdigest()
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 m=module('reload_seal_suite','research/verify-world-reload.py');cross=module('reload_seal_digest','research/summarize-portable-cross-gpu.py')
 r=json.loads((ROOT/'research/portable-world-reload-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=json.loads((p/'evidence.json').read_text());iw=m.INPUT*4;ow=m.OUTPUT*4
 assert r['passed'] and e==r['evidence'] and e['gpu_execution_verified'] and e['backend']=='metal' and e['transport']['device']=='Apple M5' and e['transport']['command_status']=='completed'
 assert len(data)==4+65*iw and len(raw)==65*ow and data[:4]==(65).to_bytes(4,'little') and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for path,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 host={}
 for path in ('app/portable_reload_specs.py','app/portable_runtime.py','app/portable_backend.py','app/portable_damage_specs.py','app/portable_specs.py','research/world_reload_cases.py','research/world_reload_native.py','research/verify-world-reload.py','scripts/run-metal-probe.swift'):
  b=(ROOT/path).read_bytes();assert b==subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT);host[path]=sha(b)
 rows,programs,bad=m.prepare();assert (len(rows),len(bad))==(46,19)
 for i,(c,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  actual=m.decoded(block,meta,c,bindings);native,trace=m.inspect_native(c);stored=r['cases'][i]
  assert m.charge.team.skill_trace(block,meta)==trace==stored['skill_trace']==stored['native_skill_trace']
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and actual==stored['actual'] and json.loads(json.dumps(native))==stored['native'],c['name']
  assert not any(block[m.L['COUNTER_CONTEXT_BASE']:m.L['COUNTER_CONTEXT_BASE']+1096])
 for i,(name,w) in enumerate(bad):
  at=46+i;assert struct.pack('<'+'I'*len(w),*w)==data[4+at*iw:4+(at+1)*iw] and int.from_bytes(raw[at*ow:at*ow+4],'little')==64
 generation=json.loads((ROOT/'research/portable-world-reload-generated-preservation.json').read_text());assert generation['passed'] and len(generation['cases'])==19 and generation['gpu_executions']==0
 for c in generation['cases']:
  assert c['actual']==c['expected']
  for path,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 cpu=json.loads((ROOT/'research/portable-world-reload-cpu-validation.json').read_text());assert cpu['passed'] and cpu['tests']==523 and cpu['gpu_calls']==0 and sha(cpu['output'].encode())==cpu['output_sha256'] and 'Ran 523 tests' in cpu['output'] and cpu['output'].rstrip().endswith('OK')
 for path,h in cpu['source_sha256'].items():assert sha((ROOT/path).read_bytes())==h,path
 initial=json.loads((ROOT/'research/portable-world-reload-initial-gpu.json').read_text());ip=Path(initial['captured']);old=(ip/'readback.bin').read_bytes();before=(ip/'input.bin').read_bytes();ie=json.loads((ip/'evidence.json').read_text());assert not initial['passed'] and ie==initial['evidence'] and ie['gpu_execution_verified'] and ie['transport']['command_status']=='completed'
 assert len(before)==4+62*iw and len(old)==62*ow and before[4:4+43*iw]==data[4:4+43*iw] and sha(old)==ie['output_sha256']
 for path,h in ie['source_sha256'].items():assert sha(subprocess.check_output(['git','show','dff1086:'+path],cwd=ROOT))==h,path
 failed={c['name'] for c in initial['cases'] if not c['passed']};assert failed=={'reload-stacked-fixed','reload-explicit-negative-budget-ordinary-ammo'}
 assert all(old[i*ow:(i+1)*ow]==raw[i*ow:(i+1)*ow] for i,c in enumerate(rows[:43]) if c['name'] not in failed)
 for i,(name,w) in enumerate(bad):assert before[4+(43+i)*iw:4+(44+i)*iw]==data[4+(46+i)*iw:4+(47+i)*iw] and old[(43+i)*ow:(44+i)*ow]==raw[(46+i)*ow:(47+i)*ow]
 first=json.loads((ROOT/'research/portable-world-reload-initial-transport-finding.json').read_text());fp=Path(first['captured']);assert first['gpu_executions']==0 and first['stage']=='host word-stride validation' and 'Invalid portable word strides' in first['failure']['error'] and (fp/'input.bin').read_bytes()==before and not (fp/'readback.bin').exists()
 prior=module('reload_prior_retention','research/verify-world-charge-control-short.py');entries,previous=prior.prepare();gold=json.loads(prior.GOLDEN.read_text());assert sha(previous)==gold['input_sha256'] and len(entries)==58
 for i,(name,w,domain) in enumerate(entries):
  assert gold['entries'][i]['name']==name and gold['entries'][i]['input_sha256']==sha(previous[4+i*104136*4:4+(i+1)*104136*4])
  if domain is not None:assert cross.digest(dict(zip(('battle','skill_trace'),prior.suite.inspect_native(domain[0]))))==gold['entries'][i]['native_sha256']
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),host_and_native_source_sha256=host,metal_inputs=65,native_battles=46,raw_rejections=19,portable_cpu_tests=523,frozen_gpu_source_cpu_tests=512,old19_cuda_msl_generated_exact=True,old58_input_and_native31_fingerprints_retained=True,old1063_gpu_reexecutions=0,normal4682_gpu_reexecutions=0,typed_force_reload=True,typed_absolute_reload_time=True,fixed_maximum_ignores_speed=True,direct_active_fixed_query_matches_native=True,synchronous_force_reload_cancels_charge_before_later_alias=True,physical_callback_vs_base_reload_context=True,full_reload_callbacks_complete_synchronously=True,explicit_negative_budget_disabled=True,catalog_reload_pairs=['Milk Blooming Bunny','Jill'],full_catalog_battle_certification=False,input_words=m.INPUT,output_words=m.OUTPUT,context_mode=22,abi='0x5045568b',stage_gpu_executions=2,stage_fixed_commits=3,initial_host_stride_rejection_gpu0=True,initial_two_gpu_differences_preserved=True,unchanged_gpu_retries=0,audit_gpu_calls=0,input_sha256=sha(data),output_sha256=sha(raw),normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-reload-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal65/native46/raw19;old19 generated;prior58/native31 audited;GPU0')
if __name__=='__main__':main()
