import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'research/detail-expansion-next.json';n=json.loads(p.read_text(encoding='utf-8'));w=n['current_work']
w.update(verification_status='First full discovery terminal1: 111/112 passed; one deferred B3 scaling_ref hit-count regression. CUDA repaired; rebuild and all current-source proofs pending.',
 regression_terminal=True,regression_passed=False,regression_session=55591,regression_log='research/detail-burst-stage-tests-before-fix.log',
 build_session=25678,ptx_build='running after repair',native_build_status='old binary; rebuild after25678 finishes',
 formal_passed=False,formal_status='Historical112 passed before CUDA repair; current-source rerun required',
 all_stage_passed=False,all_stage_status='Historical32 passed before repair; current-source rerun required',
 api_status='Historical664954161 CPU matched before repair; rerun required',ui_status='Historical243679868 CPU matched before repair; final-source rerun required. Owned4332 server49363 still cached pre-repair module.',
 repair='Deferred B3 uses one hit for accepted target forms; scaling_ref multiplies coefficient only at full-burst landing. Queue preserves every reentry cast in order. same_target:X forms remain explicitly unsupported.',
 notes='Poll build25678; once terminal0 run native build sequentially. After both build manifests match repaired CU, run test_detail_damage first, then stage112/A32/API and full112 again. No live GPU verifiers remain. Never stop user4317. Do not rerun old update-burst-stage-progress.py because it describes pre-repair results.')
w['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/detail_gpu.py','app/detail_effects.cu','scripts/verify-burst-stage-detail.py','scripts/verify-all-stage-detail.py']}
n['generated_at']=datetime.now(timezone.utc).isoformat();p.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verification_status':w['verification_status'],'build_session':w['build_session']}))
