"""Record live handles without promoting an unfinished PTX run to a checkpoint."""
import json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'))
normal=json.loads((ROOT/'research/detail-normal-acceptance.json').read_text(encoding='utf-8'))
assert normal['passed'] and normal['tests_run']==77 and normal['skipped']==0
r['current_work']={'abi':'detail_boss_buffs_v32','status':'final_native_passed_ptx_verifying','objective_complete':False,'native_cases_passed':20,'normal_tests_passed':77,'long_native_battles_passed':6,'boundary_cases_passed':2,'normal_api_passed':True,'active_verifications':[{'session_id':44276,'command':'scripts/verify-boss-buffs-detail.py --backend both','log':'research/detail-boss-buffs-phase-final-verification.log','phase':'PTX driver compilation then 20 PTX cases; poll existing handle, do not duplicate'}],'completed_sessions':[8504,22336],'next_steps':['Complete PTX verification and inspect the fresh source-bound 40-case report.','Run research/finalize-boss-buffs-records.py, then research/save-boss-buffs-checkpoint.py.','Continue actual incoming combat/stealth port. CPU reference reports (19 target rules + 6 target transitions + 20 damage layers) are groundwork only.'],'additional_reference':'research/detail-incoming-target-transitions-cpu-reference.json'}
r['current_work'].update(preview={'session_id':79228,'url':'http://127.0.0.1:4332','user_port_do_not_touch':4317},regression_proofs=['research/detail-boss-buffs-rng-30.json','research/detail-boss-buffs-rng-30-full-end-damage.json','research/detail-mode-charge-restore-probe.json'],failure_archives=['research/ports/v32-before-mode-cache-fix','research/ports/v32-mode-cache-only'])
r['generated_at']=datetime.now(timezone.utc).isoformat();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('v31 checkpoint preserved; v32 PTX verification still running.')
