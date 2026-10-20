"""Seal the current transport proof after broad gates and efficiency evaluation."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ff9a10d175f266708e2d572132b045f1c04083bb';PRIOR='7492276'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 broad=load('portable-dispatch-sequence-broad-validation');transfer=load('portable-dispatch-sequence-transfer-completed');decision=load('portable-dispatch-sequence-efficiency-decision');bench=load('portable-dispatch-sequence-benchmark')
 assert broad['passed'] and broad['source_commit']==SOURCE and broad['mac_gates']==31 and broad['unit_tests']==220
 assert transfer['passed'] and transfer['source_commit']==SOURCE and transfer['remote_turn_status']=='completed' and transfer['parts']==transfer['total_parts']==1
 assert decision['passed'] and decision['efficiency_evaluated'] and not decision['production_default_changed'] and bench['passed'] and bench['all_input_and_output_bytes_equal']
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 processes=[]
 for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
  parts=line.split(None,3)
  if len(parts)!=4:continue
  pid,ppid,elapsed,command=parts
  if int(pid)==os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh','/bin/bash')):continue
  if any(x in command for x in (' research/run-',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-')):processes.append(dict(pid=int(pid),ppid=int(ppid),elapsed=elapsed,command=command))
 assert not processes,processes
 m,w,s=load('portable-combat-metal'),load('windows-portable-sequence-v64'),load('portable-dispatch-sequence-metal')
 assert m['passed'] and w['passed'] and s['passed'] and s['source_commit']==w['source_commit']==SOURCE
 assert sha(P/'windows-portable-sequence-v64.json')==transfer['decoded_sha256']
 for field in ('source_sha256','validation_sha256','input_sha256','output_sha256','actual_statuses'):assert w[field]==s[field],field
 assert m['input_sha256']==s['previous_input_sha256'] and m['output_sha256']==s['prefix_output_sha256']
 for report in (m,s):
  for group in ('source_sha256','validation_sha256'):
   for path,h in report[group].items():
    assert sha(R/path)==h,path
    assert hashlib.sha256(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=R)).hexdigest()==h,path
 for name in ('checkpoint','cuda'):(P/('portable-combat-v63-'+name+'.json')).write_bytes(subprocess.check_output(['git','show',PRIOR+':research/portable-combat-'+name+'.json'],cwd=R))
 save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-sequence-v64.json',scope='Actual2050 CUDA readbacks in three dispatches; all2006 current core inputs are its byte-identical prefix. This report retains actual2050 dimensions and does not masquerade as a single2006 dispatch.'))
 old=load('portable-combat-v63-checkpoint');checkpoint=dict(old)
 checkpoint.update(verified_commit=SOURCE,previous_checkpoint=dict(report='portable-combat-v63-checkpoint.json',proof_commit=PRIOR),validation_receipt='portable-dispatch-sequence-validation.json',cuda_report='portable-combat-cuda.json',windows_report='windows-portable-sequence-v64.json',windows_execution=w['execution'],windows_postcheck=w['postcheck'],windows_checks_this_stage=1,cuda_verification_mode='all2006_core_inputs_in2050_input_three_dispatch_sequence',current_full_cuda_core_executed=True,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_source_commit=SOURCE,windows_source_commit=SOURCE,unchanged_gpu_source_prior_proof=PRIOR),mac_gates=31,unit_tests=220,real_roster_profiles=86,full_goal_complete=False,full_character_verified=0,all_characters_supported=False,normal_ui_connected=False,normal_ui_backend='cpu')
 # A historical one-dispatch claim must not survive the new sequence mode.
 checkpoint.pop('current_full_cuda_batch_executed',None)
 checkpoint['generated_source_comparison']='portable-dispatch-sequence-transfer-completed.json';checkpoint['existing_parity']='portable-dispatch-sequence-broad-validation.json'
 checkpoint['dispatch_sequence']=dict(programs=2050,dispatch_counts=[1024,1024,2],prior_core_programs=2006,additional_repeats=44,metal_report='portable-dispatch-sequence-metal.json',windows_report='windows-portable-sequence-v64.json',all_ordered_input_output_bytes_equal=True,pipeline_context_instances=1,reused_wire_buffers=2,gpu_private_fields_added=0,default_batch_capacity=2048,host_retains_all_readbacks=True,efficiency=decision)
 for field in ('source_sha256','validation_sha256','input_sha256','output_sha256','batch_layout'):checkpoint[field]=m[field]
 checkpoint['next_work']=['Connect element_code_override and other remaining effects/world scheduling, using bounded dispatch sequences without removing regression cases; certify all203 characters and all variants']
 save('portable-combat-checkpoint',checkpoint)
 save('portable-dispatch-sequence-final-processes',dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),verification_processes=processes,windows_execution_and_transfer_terminal=True))
 reports=['portable-combat-checkpoint','portable-combat-v63-checkpoint','portable-combat-v63-cuda','portable-combat-metal','portable-combat-cuda','portable-dispatch-sequence-metal','windows-portable-sequence-v64','portable-dispatch-sequence-transfer-completed','portable-dispatch-sequence-global-gates','portable-dispatch-sequence-broad-validation','portable-dispatch-sequence-timing-order','portable-dispatch-sequence-benchmark','portable-dispatch-sequence-efficiency-decision','portable-dispatch-sequence-final-processes','portable-roster-battles-metal','portable-api-metal','portable-catalog-readiness','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-stack-numeric-metal','portable-stack-notices-metal','portable-enemy-code-real-metal','portable-enemy-codes-native','portable-named-states-native','portable-instant-lists-native','portable-protection-native','portable-split-native','portable-element-override-native-characterization']
 tools=['verify-dispatch-sequence.py','run-sequence-gates.py','seal-sequence-gates.py','seal-sequence-cuda.py','benchmark-dispatch-sequence.py','finalize-sequence-proof.py','characterize-element-override.py'];docs=['portable-dispatch-sequence.md','mac-handoff.md','mac-migration.md','portable-combat-runtime.md']
 receipt=dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=SOURCE,previous_proof_commit=PRIOR,core_programs=2006,sequence_programs=2050,mac_gates=31,unit_tests=220,real_roster_profiles=86,current_full_cuda_core_executed=True,efficiency_evaluated=True,production_default_changed=False,normal_ui_backend='cpu',full_character_verified=0,full_goal_complete=False,artifact_scope=dict(current='Current transport source,2006-input core,2050-input sequence and31 gates',historical='Prior receipts are authoritative in their own proof commits',next_effect='Element override characterization is CPU-only; GPU admission remains disabled'),artifact_sha256={'research/'+n+'.json':sha(P/(n+'.json')) for n in reports},tool_sha256={'research/'+n:sha(P/n) for n in tools},documentation_sha256={'docs/'+n:sha(R/'docs'/n) for n in docs})
 save('portable-dispatch-sequence-validation',receipt);print('Current2050-input CUDA/Metal transport and31 gates sealed; full catalog remains incomplete')
if __name__=='__main__':main()
