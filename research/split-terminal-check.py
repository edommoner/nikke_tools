"""Completion barrier before split efficiency work, including remote transfer."""
import argparse,datetime,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
a=argparse.ArgumentParser();a.add_argument('--windows-report',default='windows-portable-combat-v59');a.add_argument('--timing-order',action='store_true');args=a.parse_args()
load=lambda n:json.loads((P/(n+'.json')).read_text())
probe=load('portable-instant-list-admission-probe-metal');assert probe['full_instant_list_supported'],'Resolve the instantaneous ordered-target boundary before efficiency work'
g=load('portable-split-global-gates');assert g['passed'] and g['complete'] and len(g['gates'])==25
m=load('portable-combat-metal');w=load(args.windows_report);t=load('portable-split-transfer-completed')
assert w['passed'] and w['current_full_cuda_batch_executed'] and w['execution']['exit_code']==0 and not w['execution']['timed_out'] and w['postcheck']['remaining_verification_processes']==0
assert t['passed'] and t['remote_turn_status']=='completed' and t['parts']==t['total_parts'] and t['windows_execution_terminal'] and t['windows_report']==args.windows_report+'.json'
for key in ('source_sha256','validation_sha256','input_sha256','output_sha256','actual_statuses','expected_statuses'):assert m[key]==w[key],key
source=w['execution']['commit'];subprocess.run(['git','diff','--exit-code',source,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
assert g['source_commit']==source and all(r['source_commit']==source for r in g['gates'])
processes=[]
for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
 f=line.split(None,3)
 if len(f)!=4:continue
 pid,ppid,elapsed,command=f
 if int(pid)==os.getpid() or command.startswith(('/bin/zsh','/bin/bash')):continue
 if any(k in command for k in (' research/run-split-gates.py',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-split.py')):processes.append(dict(pid=pid,elapsed=elapsed,command=command))
assert not processes,processes
name='portable-split-timing-order' if args.timing_order else 'portable-split-final-processes'
if args.timing_order:assert not (P/(name+'.json')).exists()
x=dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=source,all_mac_gates_complete=True,mac_gates=25,windows_execution_and_transfer_terminal=True,windows_report=args.windows_report+'.json',verification_processes=processes,transfer=t)
(P/(name+'.json')).write_text(json.dumps(x,indent=2)+'\n');print(name,'verified')
