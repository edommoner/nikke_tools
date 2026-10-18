import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'))
r['current_work']['active_verifications']={'native_build_session':93377,'native_build_log':'research/detail-boss-buffs-phase-fixed-build-native.log'}
r['current_work']['verification_sequence']=[
 'Wait for session 93377 to finish successfully. Never edit app/detail_effects.cu while its build is running (manifest hashes source at end).',
 'Run research/check-mode-cache-candidate.py. Its diagnostics exit zero even for a mismatch: explicitly inspect both detail-boss-buffs-rng-30*.json for first_difference=null and equal totals, plus detail-mode-charge-restore-probe.json passed=true.',
 'Run scripts/debug-boss-buff-rng.py --duration 180 and inspect first_difference and total equality. Keep any failing case; do not narrow the goal or remove the scenario.',
 'Run scripts/verify-boss-buffs-detail.py --backend both: expect 40 native/PTX cases. Run scripts/verify-normal-detail.py: expect 77 tests. Keep at most two heavy GPU processes active.',
 'Run research/verify-boss-buffs-tail.py sequentially: 6 long native cases, 2 boundary cases (32 patterns plus fixed parts; dense version reaches definition 255), then local API smoke on 4333.',
 'All reports currently from before the two cache fixes are stale by source hash. Do not publish the v32 checkpoint based on them. The old verified checkpoint remains v31.',
 'When fresh checks pass, update README evidence and boss-gpu-integration-notes status (nested target function is _attack_targets). Save with research/save-boss-buffs-checkpoint.py; all-character/effect objective remains incomplete.',
 'Continue into actual incoming target/combat semantics including stealth. Rosanna is still rejected and coverage remains 135/203 defaults, 529/812 favorite contexts. CPU incoming target audit 19 cases is groundwork, not GPU success.'
 ]
r['current_work']['preview']={'owned_server_session':79228,'url':'http://127.0.0.1:4332','user_4317':'Do not stop or restart the user server.'}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
