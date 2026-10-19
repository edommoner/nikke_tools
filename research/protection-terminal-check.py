"""Explicit completion barrier before any protection efficiency dispatch."""
import argparse,datetime,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path.insert(0,str(P))
from protection_source_equivalence import equivalence
a=argparse.ArgumentParser();a.add_argument('--timing-order',action='store_true');a.add_argument('--windows-report',default='windows-portable-combat-v58');args=a.parse_args()
load=lambda n:json.loads((P/(n+'.json')).read_text())
g=load('portable-protection-global-gates');assert g['passed'] and g['complete'] and len(g['gates'])==24
w=load(args.windows_report);t=load('portable-protection-transfer-completed');m=load('portable-combat-metal')
assert w['passed'] and w['current_full_cuda_batch_executed'] and w['execution']['exit_code']==0 and not w['execution']['timed_out'] and w['postcheck']['remaining_verification_processes']==0
assert t['passed'] and t['remote_turn_status']=='completed' and t['parts']==t['total_parts'] and t['windows_execution_terminal']
for key in ('source_sha256','validation_sha256','input_sha256','output_sha256','actual_statuses','expected_statuses'):assert w[key]==m[key],key
source_equivalence=equivalence(w['execution']['commit'])
processes=[]
for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
 fields=line.split(None,3)
 if len(fields)!=4:continue
 pid,ppid,elapsed,command=fields
 if int(pid)==os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh','/bin/bash')):continue
 if any(t in command for t in (' research/run-protection-gates.py',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-protection.py')):processes.append(dict(pid=int(pid),ppid=int(ppid),elapsed=elapsed,command=command))
assert not processes,processes
x=dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),all_mac_gates_complete=True,mac_gates=24,windows_report=args.windows_report+'.json',windows_execution_and_transfer_terminal=True,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),windows_source_commit=w['execution']['commit'],source_equivalence=source_equivalence,verification_processes=processes,transfer=t)
name='portable-protection-timing-order' if args.timing_order else 'portable-protection-final-processes'
if args.timing_order:assert not (P/(name+'.json')).exists()
(P/(name+'.json')).write_text(json.dumps(x,indent=2)+'\n');print(name,'verified')
