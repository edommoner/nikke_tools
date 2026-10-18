"""Record actually observed ordinary Tia/Cover-cube UI checks."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path='research/detail-cover-capacity-api-verification.json';api=json.loads((ROOT/path).read_text(encoding='utf-8'))
assert api['passed'] and api['pure_gpu_path_verified'] and api['abi']=='detail_cover_capacity_v37'
assert api['total']==126240621 and api['original_total']==124093862 and api['delta']==2146759
members={'티아':17961681,'리타':14084330,'크라운':14317547,'앨리스':39768548,'모더니아':40108515};assert sum(members.values())==api['total']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();assert all(sha(p)==h for p,h in api['source_sha256'].items())
files=set(api['source_sha256'])|{path,'research/detail-cover-capacity-ui-fixture.json','research/record-cover-capacity-browser-proof.py'}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,abi=api['abi'],objective_complete=False,browser_interaction_verified=True,browser='Codex In-app Browser',url='http://127.0.0.1:4332/#results',fictional_owned_data=True,live_account_import_verified=False,restored_owned_characters=5,temporary_stat_deltas={'티아':dict(atk=12000,hp=100000,**{'def':250})},observed_skills=[7,5,9],observed_cube='렐릭 커버 큐브',observed_cube_level=4,total=api['total'],original_total=api['original_total'],delta=api['delta'],members=members,CPU_verified_UI=True,pure_GPU_UI=True,source_sha256={p:sha(p) for p in sorted(files)})
(ROOT/'research/detail-cover-capacity-browser-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Recorded ordinary Tia UI acceptance; full goal incomplete.')
