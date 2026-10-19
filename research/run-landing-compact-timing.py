"""Start sequential timings only after saved correctness and transfer gates."""
import datetime,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
reports=['portable-combat-metal','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-landing-compact-unit-tests','portable-generated-v41-comparison']
for n in reports:assert json.loads((P/(n+'.json')).read_text())['passed'],n
w=json.loads((P/'windows-portable-combat-v41.json').read_text());assert w['execution']['exit_code']==0 and w['postcheck']['remaining_verification_processes']==0
# The transfer end is independently observed by the coordinator, not inferred
# from these report files. Require its saved terminal-turn receipt explicitly.
t=json.loads((P/'portable-landing-compact-transfer-completed.json').read_text());assert t['turn_status']=='completed' and t['thread_status']=='idle' and t['saved_parts']==21
raw=subprocess.check_output(['ps','-axo','pid=,comm=,args='],text=True);remaining=[]
for line in raw.splitlines():
 fields=line.strip().split(None,2)
 if len(fields)<3:continue
 pid,comm,args=fields
 if int(pid)==os.getpid():continue
 if ('Python' in comm or 'python' in comm or 'swift-frontend' in comm) and any(s in args for s in ('scripts/verify-portable','research/verify-landing-compact','scripts/run-metal-probe.swift')):remaining.append(line)
assert not remaining,remaining
receipt=dict(passed=True,before_timing_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verification_processes=remaining,windows_execution_and_transfer_terminal=True,windows_turn=t['turn_id'],sequential=True,commands=[])
for workload in ('two-receipts','full-2048'):
 for label in ('wide','compact'):
  cmd=[sys.executable,str(P/'benchmark-landing-compact.py'),'--workload',workload,'--label',label]
  subprocess.run(cmd,cwd=R,check=True);receipt['commands'].append(dict(workload=workload,label=label,exit_code=0))
receipt['after_timing_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(P/'portable-landing-compact-timing-order.json').write_text(json.dumps(receipt,indent=2)+'\n')
