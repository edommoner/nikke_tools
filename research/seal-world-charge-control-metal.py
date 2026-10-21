"""Audit captured manual-control Metal evidence and prior fingerprints;GPU0."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='2a585cf'
def sha(b):return hashlib.sha256(b).hexdigest()
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 m=module('charge_control_seal','research/verify-world-charge-control.py');cross=module('charge_control_digest','research/summarize-portable-cross-gpu.py')
 r=json.loads((ROOT/'research/portable-world-charge-control-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=json.loads((p/'evidence.json').read_text());iw=m.INPUT*4;ow=655360*4
 assert r['passed'] and e==r['evidence'] and e['gpu_execution_verified'] and e['backend']=='metal' and e['transport']['device']=='Apple M5' and e['transport']['command_status']=='completed'
 assert len(data)==4+58*iw and len(raw)==58*ow and data[:4]==(58).to_bytes(4,'little') and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for path,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 host={}
 for path in ('app/portable_charge_control_specs.py','app/portable_runtime.py','app/portable_runtime_layout.py','app/portable_trigger_specs.py','app/portable_specs.py','research/world_charge_control_cases.py','research/world_charge_control_native.py','research/world_frame_native.py','research/world_team_native.py','research/verify-world-charge-control.py'):
  b=(ROOT/path).read_bytes();assert b==subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT);host[path]=sha(b)
 rows,programs,bad=m.prepare();assert (len(rows),len(bad))==(31,27)
 for i,(c,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  actual=m.decoded(block,meta,c,bindings);native,trace=m.inspect_native(c);stored=r['cases'][i]
  assert m.team.skill_trace(block,meta)==trace==stored['skill_trace']==stored['native_skill_trace']
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and actual==stored['actual'] and json.loads(json.dumps(native))==stored['native'],c['name']
  assert not any(block[m.L['COUNTER_CONTEXT_BASE']:m.L['COUNTER_CONTEXT_BASE']+1096])
 for i,(name,w) in enumerate(bad):
  at=31+i;assert struct.pack('<'+'I'*len(w),*w)==data[4+at*iw:4+(at+1)*iw] and int.from_bytes(raw[at*ow:at*ow+4],'little')==64
 g=json.loads((ROOT/'research/portable-world-charge-control-generated-preservation.json').read_text());assert g['passed'] and len(g['cases'])==18 and g['gpu_executions']==0
 for c in g['cases']:
  assert c['actual']==c['expected']
  for path,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 cpu=json.loads((ROOT/'research/portable-world-charge-control-cpu-validation.json').read_text());unit=cpu['output'];assert cpu['passed'] and cpu['tests']==488 and cpu['gpu_calls']==0 and sha(unit.encode())==cpu['output_sha256'] and 'Ran 488 tests' in unit and unit.rstrip().endswith('OK')
 initial=json.loads((ROOT/'research/portable-world-charge-control-initial-metal.json').read_text());ip=Path(initial['captured']);old=(ip/'readback.bin').read_bytes();ie=json.loads((ip/'evidence.json').read_text());assert not initial['passed'] and ie==initial['evidence'] and ie['gpu_execution_verified'] and ie['transport']['command_status']=='completed'
 assert (ip/'input.bin').read_bytes()==data and len(old)==len(raw) and sha(old)==ie['output_sha256']
 for path,h in ie['source_sha256'].items():assert sha(subprocess.check_output(['git','show','a9b7c2a:'+path],cwd=ROOT))==h,path
 failed={c['name'] for c in initial['cases']+initial['rejected_cases'] if not c['passed']};assert failed=={'manual-charge-callback-removes-ammo-while-holding','manual-charge-callback-enters-auto-mode','manual-charge-ammo-removal-retains-charge-for-second-alias'}
 assert all(old[i*ow:(i+1)*ow]==raw[i*ow:(i+1)*ow] for i,c in enumerate(rows) if c['name'] not in failed)
 second=json.loads((ROOT/'research/portable-world-charge-control-second-metal.json').read_text());sp=Path(second['captured']);sr=(sp/'readback.bin').read_bytes();se=json.loads((sp/'evidence.json').read_text())
 assert not second['passed'] and se==second['evidence'] and (sp/'input.bin').read_bytes()==data and sha(sr)==se['output_sha256']
 for path,h in se['source_sha256'].items():assert sha(subprocess.check_output(['git','show','f077cbe:'+path],cwd=ROOT))==h,path
 assert [c['name'] for c in second['cases'] if not c['passed']]==['manual-charge-callback-enters-auto-mode']
 assert all(sr[i*ow:(i+1)*ow]==raw[i*ow:(i+1)*ow] for i,c in enumerate(rows) if c['name']!='manual-charge-callback-enters-auto-mode')
 prior=module('prior_team_retention','research/verify-world-team-short.py');entries,before=prior.prepare();gold=json.loads(prior.GOLDEN.read_text());assert sha(before)==gold['input_sha256'] and len(entries)==47
 for i,(name,w,domain) in enumerate(entries):
  assert gold['entries'][i]['name']==name and gold['entries'][i]['input_sha256']==sha(before[4+i*98000*4:4+(i+1)*98000*4])
  if domain is not None:assert cross.digest(dict(zip(('battle','skill_trace'),prior.suite.inspect_native(domain[0]))))==gold['entries'][i]['native_sha256']
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),host_and_native_source_sha256=host,metal_inputs=58,native_battles=31,raw_rejections=27,portable_cpu_tests=488,old18_cuda_msl_generated_exact=True,old47_input_and_native29_fingerprints_retained=True,old1005_gpu_reexecutions=0,normal4682_gpu_reexecutions=0,typed_manual_charge_hold=True,raw_threshold_aliases_preserved=True,full_charge_clock_latched=True,per_charge_consumption_before_conditions=True,dynamic_camera_arbitration=True,policy_anchor_reentry_bounded=True,input_words=m.INPUT,output_words=655360,context_mode=21,abi='0x5045568a',stage_gpu_executions=3,stage_gpu_sources=3,initial_three_gpu_differences_preserved=True,unchanged_gpu_retries=0,audit_gpu_calls=0,input_sha256=sha(data),output_sha256=sha(raw),normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-charge-control-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal58/native31/raw27;old18 strict generated;prior47/native29 audited;GPU0')
if __name__=='__main__':main()
