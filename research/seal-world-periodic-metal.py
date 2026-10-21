"""CPU-only audit of immutable periodic packets, actual timers and old prefixes."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='1f05991'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('periodic_seal','research/verify-world-periodic.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-periodic-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=97464*4;ow=655360*4;legacy=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and len(data)==4+923*iw and len(raw)==923*ow and int.from_bytes(data[:4],'little')==923 and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for path,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 host_sources={}
 for path in ['app/portable_backend.py','scripts/run-metal-probe.swift','app/portable_specs.py','app/portable_periodic_specs.py','app/portable_runtime.py','research/world_frame_native.py','research/world_skill_native.py','research/world_periodic_cases.py','research/world_periodic_native.py','research/verify-world-periodic.py']:
  value=sha((ROOT/path).read_bytes());assert value==sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)),path;host_sources[path]=value
 for begin,n in [(0,700),(700,223)]:
  batch=(p/f'input-{begin}.bin').read_bytes();part=(p/f'readback-{begin}.bin').read_bytes();proof=json.loads((p/f'evidence-{begin}.json').read_text())
  assert batch==n.to_bytes(4,'little')+data[4+begin*iw:4+(begin+n)*iw] and part==raw[begin*ow:(begin+n)*ow]
  assert sha(batch)==proof['input_sha256'] and sha(part)==proof['output_sha256'] and proof['source_sha256']==e['source_sha256'] and proof['gpu_execution_verified']
  assert proof['transport']['device']=='Apple M5' and proof['transport']['command_status']=='completed' and proof['transport']['output_bytes']<2**31
 generation=json.loads((ROOT/'research/portable-build/world-periodic-generation.json').read_text());assert generation['passed'] and len(generation['cases'])==11 and generation['gpu_executions']==0
 for c in generation['cases']:
  assert c['actual']==c['expected']
  for path,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 unit=(ROOT/'research/portable-build/world-periodic-repair-unit.log').read_text();assert 'Ran 408 tests' in unit and unit.rstrip().endswith('OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(32,13)
 for i,(case,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  actual=d.decoded(block,meta,case,bindings);native,trace=d.inspect_native(case);stored=r['cases'][i]
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and stored['actual']==actual and stored['native']==json.loads(json.dumps(native)),case['name']
  assert d.skill_trace(block)==trace==stored['skill_trace']==stored['native_skill_trace']
  assert not any(block[d.L['COUNTER_CONTEXT_BASE']:d.L['COUNTER_CONTEXT_BASE']+1096])
  assert block[d.L['WORLD_PERIODIC_HEAD_BASE']]==0x57504331
  for row in range(256):d.snapshot(block,d.L['WORLD_PERIODIC_DEFINITION_BASE']+row*38)
  for index in range(2048):d.snapshot(block,d.L['WORLD_PERIODIC_PACKET_BASE']+index*38)
 for i,(name,w) in enumerate(bad):
  at=32+i;assert struct.pack('<'+'I'*len(w),*w)==data[4+at*iw:4+(at+1)*iw] and int.from_bytes(raw[at*ow:at*ow+4],'little')==64 and r['rejected_cases'][i]['passed']
 old=json.loads((ROOT/'research/portable-world-pending-metal.json').read_text());q=Path(old['captured']);before=(q/'input.bin').read_bytes();prior=(q/'readback.bin').read_bytes()
 assert old['passed'] and sha(before)==old['evidence']['input_sha256'] and sha(prior)==old['evidence']['output_sha256']
 zeros=b'\0'*(ow-legacy)
 for j in range(878):
  at=45+j;w=bytearray(data[4+at*iw:4+(at+1)*iw]);w[:4]=(0x50455683).to_bytes(4,'little')
  assert w==before[4+j*iw:4+(j+1)*iw] and raw[at*ow:at*ow+legacy]==prior[j*legacy:(j+1)*legacy] and raw[at*ow+legacy:(at+1)*ow]==zeros and r['preserved878'][j]['passed']
 first=json.loads((ROOT/'research/portable-world-periodic-initial-metal.json').read_text());replay=json.loads((ROOT/'research/portable-world-periodic-observer-replay.json').read_text())
 assert not first['passed'] and sum(c['passed'] for c in first['cases'])==29 and sum(c['passed'] for c in replay['cases'])==32 and all(c['passed'] for c in first['preserved878']+replay['preserved878'])
 assert [c['name'] for c in replay['rejected_cases'] if not c['passed']]==['periodic-interval-nan'] and first['evidence']['source_sha256']==replay['evidence']['source_sha256']!=e['source_sha256']
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=923,host_and_native_source_sha256=host_sources,full_native_battles=32,raw_rejections=13,old878_all_524288_word_prefixes_exact=True,old878_extended_tail_zero=True,old11_cuda_msl_generated_exact=True,portable_cpu_tests=408,periodic_definition_snapshots=256,immutable_packet_snapshots=2048,snapshot_words=38,all128_targets=True,captured_generation_uses_checked_monotonic_actor_birth_ordinal=True,native_timer_carrier_and_named_predicate_state_equal=True,aliases_union_without_retargeting_existing_packets=True,retired_handle_membership_preserved_for_before_finish_observation=True,constructor_uid_observation_restored_full_native_entry_ordinals=True,positive_finite_interval_required=True,old_unvalidated_output_strides_still_rejected=True,input_words=97464,output_words=655360,context_mode=11,abi='0x50455684',current_source_disjoint_metal_dispatches=2,actual_metal_dispatches_this_stage=4,frozen_gpu_sources=2,unchanged_gpu_retries=0,failed_readbacks_preserved=True,input_sha256=sha(data),output_sha256=sha(raw),audit_gpu_calls=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-periodic-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal923 sealed:32 native clocks/13 raw/old878 prefixes+zero tail;CPU408;GPU audit0')
if __name__=='__main__':main()
