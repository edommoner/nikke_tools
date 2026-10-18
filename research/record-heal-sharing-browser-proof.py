"""Record the actually observed ordinary v41 UI, not inferred execution."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p='research/detail-heal-sharing-api-verification.json';api=json.loads((ROOT/p).read_text(encoding='utf-8'))
assert api['passed'] and api['pure_gpu_path_verified'] and api['abi']=='detail_heal_sharing_v41'
assert (api['original_total'],api['total'],api['delta'])==(94476142,98154067,3677925)
observed={'렘':33274218,'마르차나':11345950,'리타':7654425,'앨리스':19704854,'모더니아':26174620}
assert sum(observed.values())==api['total'] and observed=={r['name']:r['damage'] for r in api['members']}
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();assert all(sha(p)==h for p,h in api['source_sha256'].items())
files=set(api['source_sha256'])|{p,'research/detail-heal-sharing-ui-fixture.json','research/record-heal-sharing-browser-proof.py'}
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,abi=api['abi'],objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,browser_interaction_verified=True,browser='Codex In-app Browser',url='http://127.0.0.1:4332/#results',fictional_owned_data=True,live_account_import_verified=False,restored_owned_characters=5,observed_skills=[7,5,9],observed_cube='렐릭 힐링 큐브',observed_cube_level=4,temporary_stat_deltas={'렘':{'atk':12000,'hp':100000,'def':250}},pure_gpu_button_execution_verified=True,pure_gpu_total=98154067,pure_gpu_original_total=94476142,pure_gpu_delta=3677925,pure_gpu_badge_without_CPU_verification=True,verified_gpu_button_execution_verified=True,verified_gpu_total=98154067,verified_gpu_original_total=94476142,verified_gpu_delta=3677925,verified_gpu_badge_with_CPU_verification=True,observed_member_damage=observed,observed_conditions='30s / level400 / enemyDEF31784 / character shooting / auto burst / accumulated gauge / seed12345',result_tab_left_open=True,screenshot_observed=True,screenshot_local_file_not_created=True,speedup_claim=False,source_sha256={p:sha(p) for p in sorted(files)})
(ROOT/'research/detail-heal-sharing-browser-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,pure_gpu_total=98154067,verified_gpu_total=98154067,objective_complete=False)))
