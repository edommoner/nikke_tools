"""Record observed ordinary v40 UI, not inferred browser execution."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path='research/detail-healing-storage-api-verification.json';api=json.loads((ROOT/path).read_text(encoding='utf-8'))
assert api['passed'] and api['pure_gpu_path_verified'] and api['abi']=='detail_healing_storage_v40'
assert api['total']==92423691 and api['original_total']==89771061 and api['delta']==2652630
members={'마르차나':24308810,'프리카':7310858,'리타':8821097,'앨리스':23163203,'모더니아':28819723};assert sum(members.values())==api['total']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();assert all(sha(p)==h for p,h in api['source_sha256'].items())
files=set(api['source_sha256'])|{path,'research/detail-healing-storage-ui-fixture.json','research/record-healing-storage-browser-proof.py'}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,abi=api['abi'],objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,browser_interaction_verified=True,browser='Codex In-app Browser',url='http://127.0.0.1:4332/#results',fictional_owned_data=True,live_account_import_verified=False,restored_owned_characters=5,temporary_stat_deltas={'마르차나':dict(atk=12000,hp=100000,**{'def':250})},observed_skills=[7,5,9],observed_cube='렐릭 힐링 큐브',observed_cube_level=4,observed_burst_gauge_mode='accumulate',total=api['total'],original_total=api['original_total'],delta=api['delta'],members=members,CPU_verified_UI=True,pure_GPU_UI=True,source_sha256={p:sha(p) for p in sorted(files)})
(ROOT/'research/detail-healing-storage-browser-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Recorded observed storage GPU-only and CPU-verified UI results; full goal incomplete.')
