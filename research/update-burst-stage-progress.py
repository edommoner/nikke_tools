"""Record live handles and evidence without treating an in-progress run as passed."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
p=ROOT/'research/detail-burst-stage-verification.log';b=p.read_bytes();s=b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
rows=[json.loads(line) for line in s.splitlines() if line.startswith('{')]
n=read('research/detail-expansion-next.json');w=n['current_work']
w.update(native_build_status='completed',formal_session=81550,formal_log='research/detail-burst-stage-verification.log',formal_report='research/detail-burst-stage-verification.json',formal_expected_cases=112,
         verification_status='Formal112 and A-stage32 passed; regression112 still running',
         formal_terminal=True,formal_passed=True,all_stage_terminal=True,all_stage_passed=True,all_stage_session=28846,all_stage_log='research/detail-all-stage-verification.log',all_stage_report='research/detail-all-stage-verification.json',all_stage_expected_cases=32,
         native_cases_observed=sum(r['backend']=='native' for r in rows),ptx_cases_observed=sum(r['backend']=='ptx' for r in rows),observed_passed=sum(r['passed'] for r in rows),
         regression_session=55591,regression_log='research/detail-burst-stage-tests.log',expected_test_count=112,
         api_status='passed: native normal API compare, CPU verification, board, cache separation and unsupported fallback',api_report='research/detail-burst-stage-api-verification.json',api_total=read('research/detail-burst-stage-api-verification.json')['total'],
         node_tests_passed=20,node_report='research/detail-burst-stage-node-tests.log',favorite_contexts_compiled=443,
         ui_fixture='research/detail-burst-stage-ui-fixture.json',ui_status='Passed v18 normal UI, total243679868 CPU matched; research/detail-burst-stage-ui-verification.json. Owned4332 server session49363 and Brave tab71557210. Never stop user server4317.',
         notes='Poll exact live regression handle55591; formal81550 terminal0 passed112, A-stage28846 terminal0 passed32. Do not restart on observation timeout or edit compiler/CUDA/verifier during live runs. API smoke16467 and native build23700 terminal0. v17 checkpoint is historical; after all proofs pass use research/save-burst-stage-checkpoint.py. All-character goal remains active.')
w['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-build.json','app/detail_effects-sm86.json','scripts/verify-burst-stage-detail.py','scripts/verify-burst-gauge-detail.py']}
n['generated_at']=datetime.now(timezone.utc).isoformat()
n['next_cleanse_reference']={'path':'research/detail-cleanse-cpu-references.json','semantics':'research/detail-cleanse-semantics.json','cases':22,'cpu_only':True,'gpu_implemented':False,'notes':'Per-recipient oldest harmful only; no end notifications or dot timer cancellation; retain shield/bullet maps on partial removal. When a captured DoT carrier is stripped, subsequent timer damage falls back to current reference stacks rather than its stale capture. Cocoa random harmful target requires GPU PRNG parity; do not approximate leftmost.'}
n['next_harmful_random_reference']={'path':'research/detail-harmful-random-cpu-references.json','cases':9,'cpu_only':True,'gpu_implemented':False,'notes':'Authored seeds0/1/12345; empty/all-harmful/mixed-irremovable pools. Recipient observations are outputs only and cannot be supplied as GPU inputs.'}
(ROOT/'research/detail-expansion-next.json').write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in w.items() if k!='source_sha256'},ensure_ascii=True))
