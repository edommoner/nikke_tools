"""Audit scoped world-notice proof; retain pending global/CUDA/full-world work."""
import hashlib,json,subprocess,sys,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_backend import source_hashes

def load(path):return json.loads((ROOT/path).read_text())
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  while block:=stream.read(8*1024*1024):h.update(block)
 return h.hexdigest()
def previous(commit,path):return json.loads(subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT))
def equal(a,b):
 assert Path(a).read_bytes()==Path(b).read_bytes(),(a,b)
 return dict(previous=str(a),current=str(b),sha256=sha(b),all_bytes_equal=True)

def main():
 hashes=source_hashes('gpu/world_frame_entry.slang');base=load('research/portable-world-frame-metal.json');ext=load('research/portable-world-notices-extended-metal.json');zero=load('research/portable-world-zero-once-metal.json');notice=load('research/portable-world-notices-metal.json');prior=load('research/portable-world-frame-prior-metal.json')
 reports=[base,ext,zero,notice];sessions=[]
 for r in reports:
  e=r.get('evidence',r);assert r['passed'] and e['gpu_execution_verified'] and e['backend']=='metal' and e['source_sha256']==hashes
  folder=Path(r['captured']);assert sha(folder/'readback.bin')==e['output_sha256'] and sha(folder/'input.bin')==e['input_sha256'];sessions.append(str(folder))
 assert prior['passed'] and prior['complete'] and prior['programs']==4682 and prior['all_old_output_words_equal'] and len(prior['negative_cases'])==25
 for e in prior['batches']+[prior['negative_evidence']]:
  assert e['gpu_execution_verified'] and e['source_sha256']==hashes
  folder=Path(e['retained']) if 'retained' in e else Path(prior['captured'])/'negative'
  assert sha(folder/'input.bin')==e['input_sha256'] and sha(folder/'readback.bin')==e['output_sha256']
 assert len(prior['batches'])==5 and len(notice['cases'])==14 and len(notice['rejected_cases'])==9
 assert len(base['cases'])==17 and len(ext['cases'])==5 and len(zero['cases'])==4
 parity={}
 for path,current in [('research/portable-world-frame-metal.json',base),('research/portable-world-zero-extended-metal.json',ext),('research/portable-world-zero-once-metal.json',zero)]:
  old=previous('23b1628',path)
  for file in ['input.bin','readback.bin']:parity[path+':'+file]=equal(Path(old['captured'])/file,Path(current['captured'])/file)
 failed=load('research/portable-world-zero-once-finding.json');old=Path(failed['captured']);new=Path(zero['captured']);assert (old/'input.bin').read_bytes()[4:]==(new/'input.bin').read_bytes()[4:4+88848*4]
 assert failed['passed'] is False and failed['differences']==['boss_log','graph_history'] and zero['cases'][0]['passed']
 unit=Path('/tmp/nikke-world-notice-unit.log').read_text();assert 'Ran 288 tests' in unit and unit.rstrip().endswith('OK')
 core=load('research/portable-combat-metal.json');assert core['passed'] and core['gpu_execution_verified'] and core['source_sha256']==source_hashes('gpu/event_runtime.slang') and len(core['cases'])==4112 and len(core['rejected_cases'])==570
 cross=load('research/portable-cross-v79-metal-summary.json');assert cross['passed'] and cross['changed_keys']==[]
 default_input=load('research/portable-world-notices-default-input-parity.json');default_generated=load('research/portable-world-notices-default-generated-parity.json')
 assert default_input['passed'] and default_input['inputs']==4682 and default_input['all_input_bytes_equal'] and default_generated['passed']
 for row in default_generated['rows'].values():assert row['equal']
 result=dict(passed=True,scope='Scoped common world-notice correctness;not full world/catalog or CUDA certification',source_commit=subprocess.check_output(['git','rev-parse','15bcbfe'],cwd=ROOT,text=True).strip(),source_sha256=hashes,full_native_success_cases=38,explicit_capacity_failure_cases=2,raw_rejections=34,old4682_full_output_prefix_preserved=True,total_retained_programs=4756,actual_metal_sessions=10,source_sessions=sessions,prior_capture=prior['captured'],notice_regression_parity=parity,initial_zero_once_finding_resolved_by_changed_source=True,original_failed_raw_retained=str(old),original_metal14c8e2e_finding_open=True,unit_tests=288,unit_transcript=unit,cuda_verified=False,canonical_world_admission=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,efficiency_started=False,root_global52_pending=True,normal4682_input_bytes_preserved=True,normal_fixed_source_core_gpu_verified=True,normal_core_capture=core['enemy_target_existing_parity']['raw_path'],cross_gpu_compact_expected='research/portable-cross-v79-expected.json',normal_generated_cuda_and_msl_unchanged=True,updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),remaining=['Complete root4c07f45 global52 run without source mutation;integrate isolated commits after terminal','Verify final-source normal packing/code identity,appropriate Metal global regressions and one necessary short CUDA check','Connect world overlays,debuff/DoT,actors/parts/summons/control/revive and all character variants','Measure efficiency after necessary verification,transfers and jobs terminate'])
 (ROOT/'research/portable-world-notices-validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Scoped world notices verified:38 native successes,2 cap rejections,34 raw rejections,4682 preserved,288 units')
if __name__=='__main__':main()
