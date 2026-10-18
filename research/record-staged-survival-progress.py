"""Record isolated survival work without replacing the verified v33 checkpoint."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'research/detail-expansion-next.json';journal=json.loads(path.read_text(encoding='utf-8'))
reports={}
for pattern in ('detail-staged-survival-*.json','detail-staged-revival-compat-verification.json'):
    for p in (ROOT/'research').glob(pattern):
        r=json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(r,dict):continue
        reports[str(p.relative_to(ROOT))]=dict(passed=r.get('passed'),cases=len(r.get('cases',[])),planned_cases=r.get('planned_cases'),not_run_cases=r.get('not_run_cases'),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
stage=ROOT/'research/staging/v34/app'
journal['current_work']=dict(generated_at=datetime.now(timezone.utc).isoformat(),abi='detail_survival_v34',stage_path='research/staging/v34',production_abi='detail_incoming_v33',promoted=False,objective_complete=False,
    source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir() if p.is_file()},reports=reports,
    diagnosis='Fixed heal_received_pct lazy carriers with dedicated stat-scoped resolution matching CPU _live_sum. Native full 39 and healing 3, PTX healing 3 passed; initial failure is archived. Full PTX/baseline/long suites are still running.',
    process_handles=dict(native_suite=53010,ptx_warm_suite=80057,task_preview_v33=33037,preview_port=4332),
    remaining=['Finish both source-bound full survival, baseline and long-battle suites.','Install the explicit revival CPU compatibility bridge in production only with verified promotion.','Verify ordinary API execution, owned/gear deltas, and browser interaction for the promoted version.','HP-edge triggers, other unsupported characters/effects, and game-model/data gaps remain.'])
journal['generated_at']=datetime.now(timezone.utc).isoformat()
path.write_text(json.dumps(journal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded isolated v34 progress; verified v33 checkpoint retained.')
