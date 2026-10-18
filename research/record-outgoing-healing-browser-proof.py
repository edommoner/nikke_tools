"""Record the ordinary UI values actually observed for the v39 actual healer."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path='research/detail-outgoing-healing-api-verification.json';api=json.loads((ROOT/path).read_text(encoding='utf-8'))
assert api['passed'] and api['pure_gpu_path_verified'] and api['abi']=='detail_outgoing_healing_v39'
assert api['total']==91290847 and api['original_total']==88288865 and api['delta']==3001982
members={'프리카':17453587,'리타':13416821,'크라운':10250042,'모더니아':36254804,'앨리스':13915593};assert sum(members.values())==api['total']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();assert all(sha(p)==h for p,h in api['source_sha256'].items())
files=set(api['source_sha256'])|{path,'research/detail-outgoing-healing-ui-fixture.json','research/record-outgoing-healing-browser-proof.py'}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,abi=api['abi'],objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,browser_interaction_verified=True,browser='Codex In-app Browser',url='http://127.0.0.1:4332/#results',fictional_owned_data=True,live_account_import_verified=False,restored_owned_characters=5,temporary_stat_deltas={'프리카':dict(atk=12000,hp=100000,**{'def':250})},observed_skills=[7,5,9],observed_cube='렐릭 힐링 큐브',observed_cube_level=4,observed_burst_gauge_mode='accumulate',total=api['total'],original_total=api['original_total'],delta=api['delta'],members=members,CPU_verified_UI=True,pure_GPU_UI=True,source_sha256={p:sha(p) for p in sorted(files)})
(ROOT/'research/detail-outgoing-healing-browser-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Recorded observed v39 UI CPU-verified and GPU-only results. Full objective incomplete.')
