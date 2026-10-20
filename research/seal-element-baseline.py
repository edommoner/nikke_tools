"""Seal the verified baseline before adopting the selected optimization.
The initial unlocalized Metal mismatch is retained as an open finding.
"""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='14c8e2e61fd6eeb9950a13c76f217ae62ca82fd9';PRIOR='ce01fad'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 broad=load('portable-element-broad-validation');transfer=load('portable-element-transfer-completed');decision=load('portable-element-efficiency-decision');bench=load('portable-element-benchmark');m=load('portable-combat-metal');w=load('windows-portable-element-v65')
 assert broad['passed'] and broad['all_current_gates_passed'] and broad['source_commit']==SOURCE and broad['mac_gates']==31 and broad['unit_tests']==237
 assert transfer['passed'] and transfer['remote_turn_status']=='completed' and transfer['parts']==transfer['total_parts']==65
 assert decision['passed'] and decision['efficiency_evaluated'] and decision['selected_for_adoption'] and not decision['production_change_adopted'] and bench['passed'] and bench['all_2182_input_output_bytes_equal']
 assert m['passed'] and w['passed'] and w['execution']['commit']==SOURCE and m['output_sha256']==w['output_sha256']
 assert sha(P/'windows-portable-element-v65.json')==transfer['decoded_sha256']
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 for group in ('source_sha256','validation_sha256'):
  for path,h in m[group].items():
   assert sha(R/path)==h,path
   assert hashlib.sha256(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=R)).hexdigest()==h,path
 processes=[]
 for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
  parts=line.split(None,3)
  if len(parts)!=4:continue
  pid,ppid,elapsed,command=parts
  if int(pid)==os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh','/bin/bash')):continue
  if any(x in command for x in (' research/run-',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-',' research/capture-',' research/diagnose-',' research/reproduce-')):processes.append(dict(pid=int(pid),ppid=int(ppid),elapsed=elapsed,command=command))
 assert not processes,processes
 save('portable-element-baseline-processes',dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),verification_processes=processes,windows_execution_and_transfer_terminal=True))
 for name in ('checkpoint','cuda'):(P/('portable-combat-v64-'+name+'.json')).write_bytes(subprocess.check_output(['git','show',PRIOR+':research/portable-combat-'+name+'.json'],cwd=R))
 save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-element-v65.json',scope='Actual2182 CUDA inputs in three dispatches;cases.actual retains all positive decoded records,top-level duplicate results omitted by Windows transfer. Initial Metal-only unlocalized mismatch remains separately recorded.'))
 old=load('portable-combat-v64-checkpoint');checkpoint=dict(old)
 checkpoint.update(wire_abi='0x5045566B',verified_commit=SOURCE,previous_checkpoint=dict(report='portable-combat-v64-checkpoint.json',proof_commit=PRIOR),positive_cases=1848,rejections=334,batched_inputs=2182,metal_verified=True,cuda_verified=True,validation_receipt='portable-element-baseline-validation.json',cuda_report='portable-combat-cuda.json',windows_report='windows-portable-element-v65.json',windows_execution=w['execution'],windows_postcheck=w['postcheck'],windows_checks_this_stage=1,cuda_verification_mode='all2182_current_inputs_in_three_dispatches',current_full_cuda_core_executed=True,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_source_commit=SOURCE,windows_source_commit=SOURCE,raw_prior_core_preserved_from_proof=PRIOR),mac_gates=31,unit_tests=237,real_roster_profiles=86,own_effect_preflight_passed=43,full_goal_complete=False,full_character_verified=0,all_characters_supported=False,normal_ui_connected=False,normal_ui_backend='cpu',initial_metal_finding_open=True,initial_metal_finding='portable-element-initial-core-finding.json')
 checkpoint.pop('current_full_cuda_batch_executed',None)
 checkpoint['historical_dispatch_sequence']=checkpoint.pop('dispatch_sequence',{})
 checkpoint['dispatch_sequence']=dict(core_programs=2182,metal_dispatches=[2048,134],cuda_dispatches=[1024,1024,134],pipeline_context_instances=1,reused_wire_buffers=2,default_batch_capacity=2048)
 checkpoint['generated_source_comparison']='portable-element-transfer-completed.json';checkpoint['existing_parity']='portable-element-existing-metal-parity.json';checkpoint['missing_families']=load('portable-catalog-readiness')['missing_families']
 checkpoint['regressions']={k:v for k,v in m.items() if k.endswith('_cpu_regressions')}
 checkpoint['element_overrides']=dict(native_cases=156,api_cases=9,presence_stat_id=88,header_count_word=2,code_tag_zero_means_missing=True,native_periodic_pre_expiry_presence=True,lazy_markers_not_forced=True,original_alias_code_retained=True,physical_bullet_lifetimes=True,private_fields_added=0,efficiency=decision,optimized_source_verification_pending=True)
 for field in ('source_sha256','validation_sha256','input_sha256','output_sha256','batch_layout'):checkpoint[field]=m[field]
 checkpoint['next_work']=['Adopt the selected scalar element accessors and verify the optimized source on both GPUs','Connect probability and remaining effects/world scheduling;certify all203 characters and all variants','Keep strict readback capture;initial mismatch is unlocalized and not claimed fixed']
 save('portable-combat-checkpoint',checkpoint)
 reports=['portable-combat-checkpoint','portable-combat-v64-checkpoint','portable-combat-v64-cuda','portable-combat-metal','portable-combat-cuda','windows-portable-element-v65','portable-element-transfer-completed','portable-element-existing-metal-parity','portable-element-global-gates','portable-element-initial-core-finding','portable-element-old-output-diagnostic','portable-element-reproduction','portable-element-captured-global-gates','portable-element-core-readback-receipt','portable-element-broad-validation','portable-element-timing-order','portable-element-candidate-parity','portable-element-benchmark','portable-element-efficiency-decision','portable-element-baseline-output-blocks','portable-element-baseline-processes','portable-element-overrides-metal','portable-element-overrides-native','portable-element-initial-fixture-check','portable-element-periodic-expiry-finding','portable-probability-native-characterization','portable-roster-battles-metal','portable-api-metal','portable-catalog-readiness','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-stack-numeric-metal','portable-stack-notices-metal','portable-enemy-code-real-metal','portable-enemy-codes-native','portable-named-states-native','portable-instant-lists-native','portable-protection-native','portable-split-native']
 tools=['build-element-cases.py','verify-elements.py','verify-element-regression.py','run-element-gates.py','capture-element-regression.py','run-element-gates-captured.py','diagnose-element-old-output.py','reproduce-element-old-output.py','seal-element-gates.py','seal-element-cuda.py','benchmark-elements.py','build-element-output-blocks.py','seal-element-baseline.py','characterize-probability.py'];docs=['portable-element-overrides.md','mac-handoff.md','mac-migration.md','portable-combat-runtime.md']
 receipt=dict(passed=True,all_current_required_gates_passed=True,source_commit=SOURCE,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),previous_proof_commit=PRIOR,core_programs=2182,positive_cases=1848,rejections=334,element_native_cases=156,element_api_cases=9,mac_gates=31,unit_tests=237,real_roster_profiles=86,current_full_cuda_core_executed=True,efficiency_evaluated=True,candidate_selected=True,optimized_source_verification_pending=True,initial_metal_finding_open=True,root_cause_resolved=False,full_character_verified=0,full_goal_complete=False,normal_ui_backend='cpu',artifact_scope=dict(current='All2182 baseline readbacks,156 native components,86 real profiles and31 current gates',open_finding='Initial unretained Metal raw mismatch remains unlocalized;subsequent recorded runs and CUDA agree;no claim of a fix',candidate='Full2182 parity and five workloads measured;optimized source still requires both-GPU verification',next_effect='Probability characterization is CPU-only;GPU admission remains disabled'),artifact_sha256={'research/'+n+'.json':sha(P/(n+'.json')) for n in reports},tool_sha256={'research/'+n:sha(P/n) for n in tools},documentation_sha256={'docs/'+n:sha(R/'docs'/n) for n in docs})
 save('portable-element-baseline-validation',receipt);print('Baseline CUDA/Metal evidence sealed;optimization selected and initial mismatch left explicitly open')
if __name__=='__main__':main()
