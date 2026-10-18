"""Resume journal for the promoted version while the final normal suite runs."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'research/detail-expansion-next.json';r=json.loads(path.read_text(encoding='utf-8'))
r['current_work']=dict(generated_at=datetime.now(timezone.utc).isoformat(),abi='detail_survival_v34',production_abi='detail_survival_v34',promoted=True,objective_complete=False,
    validated_staging_archive='research/ports/v34-staged-verified',native_and_ptx_cases_per_backend=126,native_repeated_lethal_long_cases=4,
    api_passed=True,api_report='research/detail-survival-api-verification.json',browser_passed=True,browser_report='research/detail-survival-browser-verification.json',browser_total=71474691,
    process_handles=dict(normal_acceptance=21564,task_preview=26182,preview_port=4332),normal_log='research/detail-survival-normal-tests.log',
    remaining=['Wait for the current 87-test normal acceptance process; inspect any failure, without restarting a running test.','Once passed, run research/finalize-survival-docs.py and research/save-survival-checkpoint.py.','Keep the all-character/effect goal active; HP-edge triggers and other omitted mechanics remain.'],
    source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/engine_compat.py','app/survival_compat.py','server.mjs','web/index.html']})
path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded promoted v34; final normal acceptance is still running.')
