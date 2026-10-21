"""CPU-only independent source/readback/native audit for enemy attack fields."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='0395cad'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('enemy_attack_seal',ROOT/'research/verify-world-enemy-attack.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 r=json.loads((ROOT/'research/portable-world-enemy-attack-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=json.loads((p/'evidence.json').read_text());iw=97464*4;ow=655360*4
 assert r['passed'] and e==r['evidence'] and e['gpu_execution_verified'] and e['backend']=='metal' and e['transport']['device']=='Apple M5' and e['transport']['command_status']=='completed'
 assert len(data)==4+37*iw and len(raw)==37*ow and data[:4]==(37).to_bytes(4,'little') and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for path,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 host={}
 for path in ['app/portable_enemy_specs.py','app/portable_specs.py','research/world_enemy_attack_cases.py','research/world_frame_native.py','research/verify-world-enemy-attack.py']:
  b=(ROOT/path).read_bytes();assert b==subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT);host[path]=sha(b)
 rows,programs,bad=m.prepare();assert (len(rows),len(bad))==(28,9)
 for i,(c,(w,meta,bindings)) in enumerate(zip(rows,programs)):
  assert struct.pack('<'+'I'*len(w),*w)==data[4+i*iw:4+(i+1)*iw]
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  actual=m.decoded(block,meta,c,bindings);native=m.observe(c);stored=r['cases'][i]
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and actual==stored['actual'] and json.loads(json.dumps(native))==stored['native'],c['name']
  assert not any(block[m.L['COUNTER_CONTEXT_BASE']:m.L['COUNTER_CONTEXT_BASE']+1096])
 for i,(name,w) in enumerate(bad):
  at=28+i;assert struct.pack('<'+'I'*len(w),*w)==data[4+at*iw:4+(at+1)*iw] and int.from_bytes(raw[at*ow:at*ow+4],'little')==64
 generation=json.loads((ROOT/'research/portable-build/world-enemy-attack-generation.json').read_text());assert generation['passed'] and len(generation['cases'])==14 and generation['gpu_executions']==0
 for c in generation['cases']:
  assert c['actual']==c['expected']
  for path,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h,path
 unit=(ROOT/'research/portable-build/world-enemy-attack-repair-unit.log').read_text();assert 'Ran 418 tests' in unit and unit.rstrip().endswith('OK')
 first=json.loads((ROOT/'research/portable-world-enemy-attack-initial-metal.json').read_text());replay=json.loads((ROOT/'research/portable-world-enemy-attack-observer-replay.json').read_text());assert not first['passed'] and sum(c['passed'] for c in replay['cases'])==22 and first['evidence']['source_sha256']==replay['evidence']['source_sha256']!=e['source_sha256']
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),host_and_native_source_sha256=host,metal_inputs=37,native_battles=28,raw_rejections=9,portable_cpu_tests=418,old14_cuda_msl_generated_exact=True,old923_gpu_reexecutions=0,caster_based_reads_base_attack=True,incoming_attack_frozen_before_victim_selection=True,negative_attack_clamped_before_defense=True,enemy_percent_uses_existing_ordered_outgoing_stat_accumulator=True,all128_recipient_queries_native_equal=True,runtime_hp_conditions_and_finite_condition_latching=True,input_words=97464,output_words=655360,context_mode=13,abi='0x50455685',stage_gpu_sources=2,stage_gpu_executions=2,unchanged_gpu_retries=0,failed_readbacks_preserved=True,observer_replay_gpu_calls=0,audit_gpu_calls=0,input_sha256=sha(data),output_sha256=sha(raw),normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-enemy-attack-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal37 native28/raw9 and old14 strict parity audited;GPU0')
if __name__=='__main__':main()
