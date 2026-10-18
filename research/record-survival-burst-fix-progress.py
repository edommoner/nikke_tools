"""Record the rejected candidate and the isolated blocked-stage correction."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'research/detail-expansion-next.json';r=json.loads(path.read_text(encoding='utf-8'))
r['current_work']=dict(generated_at=datetime.now(timezone.utc).isoformat(),abi='detail_survival_v34',objective_complete=False,production_has_temporary_dynamic_stage_cpu_guard=True,production_has_temporary_lethal_hit_cpu_guard=True,production_fully_accepted=False,
    failed_normal_acceptance='research/detail-normal-acceptance.json',known_failed_burst_conditions=4,failed_candidate_archive='research/ports/v34-production-before-burst-wait-fix',stage_before_fix_archive='research/ports/v34-before-burst-wait-fix',
    fix='Keep dead actors in automatic burst candidate order/wait masks, skip only the cast; remove the generic restart of stages permanently blocked by missing candidates.',
    stage_cuda_sha256=hashlib.sha256((ROOT/'research/staging/v34/app/detail_effects.cu').read_bytes()).hexdigest(),survival_fixture_count=42,
    process_handles=dict(native_build_completed=93164,native_burst_fix_suite=41512,ptx_burst_fix_suite=31420,task_preview=13951,preview_port=4332,old_normal_suite_stopped=21564),
    stage_runner='research/verify-survival-burst-fix-suite.py',
    remaining=['Both warm burst-fix suites are running. At most two heavy GPU processes.','Do not modify the frozen staged CUDA/host/verifier sources during the suites.','Verify all burst/heal/full/regression/long reports and native repeated-long; archive the fixed closure before promoting with research/promote-survival-burst-fix.py.','Copy the fixed backend/updated production verifier and test template; remove both temporary guards by replacing the host with the staged host.','Rerun the ordinary 87-test acceptance, ordinary API and browser verification on the final corrected kernel, then update documentation/checkpoint.','The all-character/effect objective remains incomplete; HP-edge triggers and many other effects remain.'])
path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded rejected normal acceptance and the isolated burst wait correction.')
