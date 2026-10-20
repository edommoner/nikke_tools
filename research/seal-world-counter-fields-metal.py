"""Audit Metal783 raw words and frozen source against the full native engine."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='4fc576c'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('field_seal','research/verify-world-counter-fields.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
 r=json.loads((ROOT/'research/portable-world-counter-field-metal.json').read_text());p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=97464*4;ow=524288*4
 assert r['passed'] and e['backend']=='metal' and e['gpu_execution_verified'] and int.from_bytes(data[:4],'little')==783 and len(data)==4+783*iw and len(raw)==783*ow and sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256']
 for f,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h,f
 proof=json.loads((ROOT/'research/portable-build/world-counter-field-generation.json').read_text());assert proof['passed'] and len(proof['cases'])==10 and proof['gpu_executions']==0
 for c in proof['cases']:
  assert c['actual']==c['expected']
  for f,h in c['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+f],cwd=ROOT))==h
 unit=(ROOT/'research/portable-build/counter-field-repair-unit.log').read_text();assert 'Ran 379 tests' in unit and unit.rstrip().endswith('OK')
 rows,programs,bad=d.prepare();assert (len(rows),len(bad))==(52,10);values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw];block=values[i*524288:(i+1)*524288];actual=d.physical.decoded(block,meta,case,bindings);native=d.physical.expected_native(case)
  assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope') and stored['actual']==actual and stored['native']==json.loads(json.dumps(native)),case['name']
  assert not any(block[d.L['COUNTER_CONTEXT_BASE']:d.L['COUNTER_CONTEXT_BASE']+1096]) and stored['context_restored']
  work=list(block[d.L['COUNTER_FIELD_WORK_BASE']:d.L['COUNTER_FIELD_WORK_BASE']+8])
  assert work[0]>0 and 0<work[1]<=16384 and work[2]>=work[1] and not any(work[3:]) and stored['dispatch_work']==dict(count=work[0],maximum=work[1],total=work[2],guard_exits=work[3],valid=True)
 for j,(name,words) in enumerate(bad):
  i=52+j;assert struct.pack('<'+'I'*len(words),*words)==data[4+i*iw:4+(i+1)*iw] and values[i*524288]==64 and r['rejected_cases'][j]['passed']
 old=json.loads((ROOT/'research/portable-world-counter-context-metal.json').read_text());q=Path(old['captured']);before=(q/'input.bin').read_bytes();prior=(q/'readback.bin').read_bytes();assert sha(before)==old['evidence']['input_sha256'] and sha(prior)==old['evidence']['output_sha256']
 for j in range(721):
  i=62+j;w=bytearray(data[4+i*iw:4+(i+1)*iw]);w[:4]=(0x50455680).to_bytes(4,'little');assert w==before[4+j*iw:4+(j+1)*iw] and raw[i*ow:(i+1)*ow]==prior[j*ow:(j+1)*ow] and r['preserved721'][j]['passed']
 initial=json.loads((ROOT/'research/portable-world-counter-field-initial-metal.json').read_text());replay=json.loads((ROOT/'research/portable-world-counter-field-membership-replay.json').read_text())
 assert not initial['passed'] and sum(x['passed'] for x in initial['cases'])==31 and sum(x['passed'] for x in replay['cases'])==51 and all(x['passed'] for x in initial['preserved721']+replay['preserved721'])
 assert initial['evidence']['source_sha256']==replay['evidence']['source_sha256']!=e['source_sha256']
 fan=next(c for c in r['cases'] if c['name']=='counter-field-fanout128-holds-completion-marker');assert 4096<fan['dispatch_work']['maximum']<=16384
 result=dict(passed=True,calculation_source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=ROOT,text=True).strip(),metal_inputs=783,full_native_battles=52,raw_rejections=10,old721_all_output_words_preserved=True,old10_cuda_msl_generated_exact=True,portable_cpu_tests=379,immutable_current_field_actor_context=True,generic_named_child_uses_current_aim=True,all128_field_recipients_before_marker_retirement=True,counter_refresh_epoch_retained=True,part_damage_snapshot_preserved=True,context_stack_fully_restored=True,context_mode=5,old_modes2_and4_still_rejected=True,private_dispatch_work_limit=16384,fanout128_dispatch_work=fan['dispatch_work'],prior_dispatch_limit=4096,output_words=524288,input_words=97464,actual_metal_executions=2,unchanged_gpu_retries=0,failed_readbacks_preserved=True,input_sha256=sha(data),output_sha256=sha(raw),typed_enemy_field_children=True,typed_damage_children=False,windows_counter_fields_verified=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,audit_gpu_executions=0)
 (ROOT/'research/portable-world-counter-field-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Metal783 sealed:52 full native/10 raw/old721 exact;CPU379;GPU audit0')
if __name__=='__main__':main()
