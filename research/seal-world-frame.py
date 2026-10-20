"""CPU-only audit of fixed-source isolated frame/attack coupling evidence."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE='57c2a340ea4c0c13261bc2659d7e3dae28288693'
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while data:=f.read(8*1024*1024):h.update(data)
 return h.hexdigest()
def load(name):return json.loads((P/(name+'.json')).read_text())
def git(path):return subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)
def main():
 m=load('portable-world-frame-metal');e=load('portable-world-frame-extended-metal');x=load('portable-world-frame-expiry-metal');prior=load('portable-world-frame-prior-metal')
 assert all(r['passed'] and r['gpu_execution_verified'] and r['backend']=='metal' for r in [m,e,x])
 assert m['source_commit']==SOURCE and all(r['passed'] for r in m['cases']+e['cases']+x['cases'])
 assert len(m['cases'])==17 and len(e['cases'])==4 and len(x['cases'])==1
 assert sum(r['expected_status']==0 for r in e['cases'])==2 and sum(r['expected_status']==2 for r in e['cases'])==2
 assert all(r['gpu_execution_reused'] for r in [m,e,x])
 candidate=Path(m['captured']);prep=m['prepared'];assert prior['candidate']==e['candidate']==x['candidate']==str(candidate)
 for name,h in prep['added_common_modules'].items():assert sha(git('gpu/'+name))==h==file_sha(ROOT/'gpu'/name)
 for path,h in m['source_sha256'].items():
  actual=ROOT/path;assert file_sha(actual)==h,path;relative=actual.relative_to(candidate).as_posix()
  if relative=='world_frame_candidate_runtime.slang':expected=b'#include "gpu/event_runtime.slang"\n'
  else:
   expected=git(relative);patches=[p for p in prep['patches'] if p['file']==Path(relative).name]
   if patches:
    text=expected.decode().replace('\r\n','\n')
    for patch in patches:
     assert text.count(patch['old'])==patch['count'],patch['file'];text=text.replace(patch['old'],patch['new'])
    expected=text.encode()
  assert sha(expected)==h,relative
 for r in [m,e,x]:
  assert r['source_sha256']==m['source_sha256']
  for path,h in r['source_sha256_local'].items():assert file_sha(ROOT/path)==sha(git(path))==h,path
 pins=load('portable-enemy-target-scalar-broad-validation')['pinned_upstream_source_sha256']
 for path in ['research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py']:assert file_sha(ROOT/path)==pins[path]
 captures=[]
 def verify_capture(folder,evidence):
  folder=Path(folder);actual=json.loads((folder/'evidence.json').read_text());assert actual['gpu_execution_verified'] and actual['backend']=='metal' and actual['source_sha256']==m['source_sha256']
  for key in ('input_sha256','output_sha256','generated_sha256','transport'):assert actual[key]==evidence[key],key
  for name,key in [('input.bin','input_sha256'),('readback.bin','output_sha256')]:assert file_sha(folder/name)==actual[key],str(folder/name)
  captures.append(dict(folder=str(folder),programs=actual['transport']['cases'],input_sha256=actual['input_sha256'],output_sha256=actual['output_sha256']))
 for r in [m,e,x]:verify_capture(r['captured'],r)
 assert prior['complete'] and prior['programs']==4682 and prior['all_old_output_words_equal'] and not prior['changed'] and prior['all_input_words_except_valid_abi_preserved']
 assert prior['source_sha256']==m['source_sha256'] and prior['abi_counts']=={'0x50455673':4679,'0x50455670':1,'0x50455671':1,'0x50455672':1}
 assert prior['legacy_prefix_sha256']==prior['old_full_output_sha256']==load('portable-enemy-target-scalar-canonical-core')['output_sha256']
 assert sum(b['programs'] for b in prior['batches'])==4682 and len(prior['batches'])==5
 for b in prior['batches']:assert b['all_old_output_words_equal'];verify_capture(b['retained'],b)
 assert len(prior['negative_cases'])==25 and all(r['passed'] and r['status']==64 for r in prior['negative_cases'])
 verify_capture(Path(prior['captured'])/'negative',prior['negative_evidence'])
 assert len(captures)==9 and len({r['folder'] for r in captures})==9 and sum(r['programs'] for r in captures)==4729
 for backend,suffix in [('cuda','cu'),('metal','metal')]:
  digest=file_sha(P/'portable-build'/('world_frame_candidate_runtime.'+suffix));assert all(r['generated_sha256'][backend]==digest for r in [m,e,x,prior['batches'][0],prior['negative_evidence']])
 unit=Path('/tmp/nikke-world-frame-fixed-unit.log').read_text();assert 'Ran 285 tests' in unit and unit.rstrip().endswith('OK')
 allowed={'A\tapp/portable_world_schedule_specs.py','A\tgpu/world_schedule.slang','A\tgpu/world_schedule_probe.slang','A\tgpu/world_frame_addresses.slang','A\tgpu/world_frame_runtime.slang','A\ttests/test_portable_world_schedule.py','A\ttests/test_portable_world_frame_input.py'}
 changes=subprocess.check_output(['git','diff','--name-status','be5c956',SOURCE,'--','app','scripts','gpu','tests','server.mjs'],cwd=ROOT,text=True).splitlines();assert set(changes)==allowed
 for c in m['cases']+e['cases']+x['cases']:
  if c.get('expected_status',0)!=0:continue
  for key in ('damage','allies','covers','shots','ammo','hits','boss_log','rng','graph_states','graph_history'):assert c['actual'][key]==c['native'][key],(c['name'],key)
 long=next(c for c in e['cases'] if 'rollover' in c['name']);assert long['actual']['rng']['draws']==2522 and len(long['actual']['hits'])==1536
 finding=json.loads((candidate/'initial-log-label-finding.json').read_text());assert not finding['passed'] and finding['gpu_execution_verified'] and finding['source_sha256']==m['source_sha256'] and finding['input_sha256']==m['input_sha256'] and finding['output_sha256']==m['output_sha256']
 result=dict(passed=True,source_commit=SOURCE,auditor_sha256=file_sha(Path(__file__)),checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_source_reconstructed_exactly_from_fixed_source_and_declared_patches=True,canonical_compute_files_unchanged=True,legacy_programs=4682,legacy_full_output_words_equal=True,legacy_prefix_sha256=prior['legacy_prefix_sha256'],successful_full_native_world_cases=20,explicit_trace_capacity_rejections=2,raw_world_input_rejections=25,unit_tests=285,new_input_unit_tests=3,unit_output=unit,retained_gpu_sessions=9,retained_gpu_inputs=4729,captures=captures,all_source_input_readback_hashes_verified=True,initial_log_decoder_failures_retained=True,no_unchanged_gpu_retry=True,windows_used=False,efficiency_started=False,canonical_world_admission=False,canonical_source_commit='73570451569dce424667e37f4729e475ea6b0a86',canonical_abi='0x50455673',candidate_abi='0x50455674',normal_ui='CPU',full_character_verified=0,full_goal_complete=False,initial_unlocalized_metal_finding_open=True,scope='Isolated shared full-frame direct-attack coupling only;not all enemy world kinds,payloads,real roster variants or CUDA execution. All20 successful mechanical cases use actual native simulate;2 capacity cases verify failure and completed-recipient prefixes only.')
 (P/'portable-world-frame-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('Fixed frame coupling source,20 native successes,2 capacity failures,old4682 full outputs,25 raw rejections and285 units sealed;full goal incomplete')
if __name__=='__main__':main()
