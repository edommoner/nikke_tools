"""Record observed ordinary v42 UI results, not inferred browser execution."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p='research/detail-heal-charge-api-verification.json';api=json.loads((ROOT/p).read_text(encoding='utf-8'))
assert api['passed'] and api['pure_gpu_path_verified'] and api['abi']=='detail_heal_charge_v42'
assert (api['original_total'],api['total'],api['delta'])==(103169263,106676655,3507392)
observed={'델타 : 닌자 시프':23772003,'크라운':8893878,'리타':11280978,'앨리스':31867829,'모더니아':30861967}
assert sum(observed.values())==api['total'] and observed=={r['name']:r['damage'] for r in api['members']}
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();assert all(sha(p)==h for p,h in api['source_sha256'].items())
files=set(api['source_sha256'])|{p,'research/detail-heal-charge-ui-fixture.json','research/record-heal-charge-browser-proof.py'}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,abi=api['abi'],objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,browser_interaction_verified=True,browser='Codex In-app Browser',url='http://127.0.0.1:4332/#results',fictional_owned_data=True,live_account_import_verified=False,restored_owned_characters=5,observed_skills=[7,5,9],observed_cube='렐릭 힐링 큐브',observed_cube_level=4,temporary_stat_deltas={'델타 : 닌자 시프':{'atk':12000,'hp':100000,'def':250}},pure_gpu_button_execution_verified=True,pure_gpu_total=106676655,pure_gpu_original_total=103169263,pure_gpu_delta=3507392,pure_gpu_badge_without_CPU_verification=True,verified_gpu_button_execution_verified=True,verified_gpu_total=106676655,verified_gpu_original_total=103169263,verified_gpu_delta=3507392,verified_gpu_badge_with_CPU_verification=True,observed_member_damage=observed,observed_conditions='30s / level400 / enemyDEF31784 / character shooting / auto burst / accumulated gauge / seed12345',result_tab_left_open=True,screenshot_observed=True,screenshot_local_file_not_created=True,speedup_claim=False,source_sha256={p:sha(p) for p in sorted(files)})
(ROOT/'research/detail-heal-charge-browser-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,pure_gpu_total=106676655,verified_gpu_total=106676655,objective_complete=False)))
