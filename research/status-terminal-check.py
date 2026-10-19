"""Record process/transfer completion, with an explicit pre-benchmark barrier."""
import argparse,datetime,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
a=argparse.ArgumentParser();a.add_argument('--timing-order',action='store_true');args=a.parse_args()
load=lambda n:json.loads((P/(n+'.json')).read_text())
g=load('portable-status-global-gates');assert g['passed'] and g['complete'] and len(g['gates'])==23
transfers=[load(n) for n in ('portable-status-initial-transfer-completed','portable-status-snapshot-transfer-completed','portable-status-transfer-completed')]
assert all(t['passed'] and t['remote_turn_status']=='completed' and t['windows_execution_terminal'] and t['remaining_verification_processes']==0 and t['parts']==t['total_parts'] for t in transfers)
processes=[]
for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
 fields=line.split(None,3)
 if len(fields)!=4:continue
 pid,ppid,elapsed,command=fields
 if int(pid)==os.getpid():continue
 if ' - <<' in command or command.startswith(('/bin/zsh','/bin/bash')):continue
 if any(t in command for t in (' research/run-status-gates.py',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-status.py')):
  processes.append(dict(pid=int(pid),ppid=int(ppid),elapsed=elapsed,command=command))
assert not processes,processes
x=dict(passed=True,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),all_mac_gates_complete=True,mac_gates=23,windows_execution_and_transfer_terminal=True,verification_processes=processes,windows_transfers=transfers)
name='portable-status-timing-order' if args.timing_order else 'portable-status-final-processes'
if args.timing_order:assert not (P/(name+'.json')).exists()
(P/(name+'.json')).write_text(json.dumps(x,indent=2)+'\n');print(name,'verified')
