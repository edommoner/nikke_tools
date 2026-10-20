"""Verify the completed saved CUDA transfer; optionally open the timing gate."""
import argparse,datetime,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='14c8e2e61fd6eeb9950a13c76f217ae62ca82fd9';RAW='cfbf721e4be6015675358a78a4ef30c1a8afbb49d49ba0ab01e929e15b1bc292'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def main(args):
 w=load('windows-portable-element-v65');m=load('portable-combat-metal');assert hashlib.sha256((P/'windows-portable-element-v65.json').read_bytes()).hexdigest()==RAW
 e,post=w['execution'],w['postcheck'];assert w['passed'] and m['passed'] and w['gpu_execution_verified'] and e['commit']==SOURCE and e['exit_code']==0 and not e['timed_out'] and e['below_normal_priority'] and e['timeout_seconds']==120
 assert post['remaining_verification_processes']==0 and post['existing_gpu_service_preserved']
 for field in ('head','status'):assert e['original_'+field+'_before']==post['original_'+field+'_after']
 keys=['source_sha256','validation_sha256','input_sha256','output_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','cases']+[k for k in m if k.endswith('_cpu_regressions') or k.startswith('known_')]
 for key in keys:assert w[key]==m[key],key
 assert len(m['cases'])==1848 and len(m['rejected_cases'])==334 and len(m['element_override_cpu_regressions'])==156
 for group in ('source_sha256','validation_sha256'):
  for path,h in m[group].items():
   assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h,path
   assert hashlib.sha256(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=R)).hexdigest()==h,path
 spec=importlib.util.spec_from_file_location('normalizer',P/'seal-stack-increment.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);normalized={}
 for backend,suffix in [('cuda','cu'),('metal','metal')]:
  path=P/'portable-build'/('event_runtime.'+suffix);assert hashlib.sha256(path.read_bytes()).hexdigest()==m['generated_sha256'][backend]
  normalized[backend]=helper.normalized(path.read_bytes());assert normalized[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
 for key in ('prior_inputs','current_inputs','prior_input_sha256','prior_output_sha256','input_projection','all_old_output_words_equal','no_output_normalization','source_sha256','input_sha256','output_sha256','driver_sha256'):assert w['element_override_existing_parity'][key]==m['element_override_existing_parity'][key],key
 transfer=dict(passed=True,source_commit=SOURCE,remote_turn='01a15744-4e5e-77d3-91a4-18973d9a6e48',remote_turn_status='completed',parts=65,total_parts=65,decoded_sha256=RAW,windows_execution_terminal=True,windows_report='windows-portable-element-v65.json',remaining_verification_processes=0,current_full_cuda_core_executed=True,core_programs=2182,positive=1848,rejections=334,element_native_cases=156,normalized_generated_sha256=normalized,compared_keys=keys,full_output_sha256=w['output_sha256'],cuda_dispatch_counts=[d['transport']['cases'] for d in w['dispatches']],metal_dispatch_counts=[d['transport']['cases'] for d in m['dispatches']],initial_metal_finding_remains_documented=True,full_goal_complete=False,efficiency_evaluated=False)
 save('portable-element-transfer-completed',transfer)
 if args.timing_order:
  broad=load('portable-element-broad-validation');g=load('portable-element-captured-global-gates');assert broad['passed'] and broad['all_current_gates_passed'] and broad['source_commit']==SOURCE and g['passed'] and g['complete'] and len(g['gates'])==31
  subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
  processes=[]
  for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
   parts=line.split(None,3)
   if len(parts)!=4:continue
   pid,ppid,elapsed,command=parts
   if int(pid)==os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh','/bin/bash')):continue
   if any(x in command for x in (' research/run-',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-',' research/capture-',' research/diagnose-',' research/reproduce-')):processes.append(dict(pid=int(pid),ppid=int(ppid),elapsed=elapsed,command=command))
  assert not processes,processes;assert not (P/'portable-element-timing-order.json').exists()
  save('portable-element-timing-order',dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=SOURCE,mac_gates=31,all_current_mac_gates_complete=True,windows_execution_and_transfer_terminal=True,verification_processes=processes,transfer=transfer,initial_metal_finding_open=True,measurement_scope='Compare candidate only with exact2182-input output-byte guards; initial unlocalized discrepancy is retained, not claimed resolved.'))
 print('Full2182 CUDA/Metal input/output/status/native/results/source parity and65-part transfer verified')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--timing-order',action='store_true');main(p.parse_args())
