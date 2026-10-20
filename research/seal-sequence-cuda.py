"""Compare the saved Windows sequence, then optionally open the timing gate."""
import argparse,datetime,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ff9a10d175f266708e2d572132b045f1c04083bb'
RAW='9247338a2ca2e26b1f527a5c617358cc4bfa7868db68d8e20f98667fb95b41b8';TURN='01a1571a-67e3-7e90-bcdb-e889e3475450'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def main(args):
 w=load('windows-portable-sequence-v64');m=load('portable-dispatch-sequence-metal');assert hashlib.sha256((P/'windows-portable-sequence-v64.json').read_bytes()).hexdigest()==RAW
 assert w['passed'] and m['passed'] and w['gpu_execution_verified'] and m['gpu_execution_verified']
 e,post=w['execution'],w['postcheck'];assert e['commit']==SOURCE and e['exit_code']==0 and not e['timed_out'] and e['below_normal_priority'] and e['timeout_seconds']==120
 assert post['remaining_verification_processes']==0 and post['existing_gpu_service_preserved']
 for field in ('head','status'):assert e['original_'+field+'_before']==post['original_'+field+'_after']
 keys=['source_commit','previous_proof_commit','programs','prior_programs','repeated_programs','batch_size','dispatch_counts','previous_input_sha256','previous_output_sha256','prefix_output_sha256','repeat_output_sha256','all_previous_output_words_equal','repeated_output_words_equal','actual_statuses','validation_sha256','source_sha256','input_sha256','output_sha256','logical_input_hash']
 for key in keys:assert w[key]==m[key],key
 assert m['source_commit']==SOURCE and m['programs']==2050 and m['dispatch_counts']==[1024,1024,2]
 for group in ('source_sha256','validation_sha256'):
  for path,h in m[group].items():
   assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h,path
   assert hashlib.sha256(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=R)).hexdigest()==h,path
 assert len(w['dispatches'])==len(m['dispatches'])==3
 for a,b in zip(w['dispatches'],m['dispatches']):
  for key in ('source_sha256','input_sha256','output_sha256'):assert a[key]==b[key],key
  for row in (a,b):assert row['transport']['pipeline_instances']==1 and row['transport']['buffer_allocations']==2 and row['transport']['session_dispatches']==3
 spec=importlib.util.spec_from_file_location('normalizer',P/'seal-stack-increment.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);normalized={}
 for backend,suffix in [('cuda','cu'),('metal','metal')]:
  path=P/'portable-build'/('event_runtime.'+suffix);assert hashlib.sha256(path.read_bytes()).hexdigest()==m['generated_sha256'][backend]
  normalized[backend]=helper.normalized(path.read_bytes());assert normalized[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
 transfer=dict(passed=True,source_commit=SOURCE,windows_report='windows-portable-sequence-v64.json',decoded_sha256=RAW,parts=1,total_parts=1,remote_turn_status='completed',remote_turn=TURN,windows_execution_terminal=True,remaining_verification_processes=0,current_full_cuda_core_executed=True,actual_cuda_programs=2050,prior_core_programs=2006,full_core_prefix_output_sha256=w['prefix_output_sha256'],compared_keys=keys,normalized_generated_sha256=normalized)
 save('portable-dispatch-sequence-transfer-completed',transfer)
 if args.timing_order:
  broad=load('portable-dispatch-sequence-broad-validation');g=load('portable-dispatch-sequence-global-gates');assert broad['passed'] and broad['source_commit']==SOURCE and g['complete'] and g['passed'] and len(g['gates'])==31
  subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
  processes=[]
  for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
   parts=line.split(None,3)
   if len(parts)!=4:continue
   pid,ppid,elapsed,command=parts
   if int(pid)==os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh','/bin/bash')):continue
   if any(x in command for x in (' research/run-',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-')):processes.append(dict(pid=int(pid),ppid=int(ppid),elapsed=elapsed,command=command))
  assert not processes,processes;assert not (P/'portable-dispatch-sequence-timing-order.json').exists()
  save('portable-dispatch-sequence-timing-order',dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=SOURCE,mac_gates=31,all_mac_gates_complete=True,windows_execution_and_transfer_terminal=True,verification_processes=processes,transfer=transfer))
 print('2050 CUDA/Metal ordered readbacks, per-dispatch hashes, source and terminal saved transfer verified')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--timing-order',action='store_true');main(parser.parse_args())
