"""Record ordinary UI interactions actually observed via Codex In-app Browser."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path='research/detail-survival-scaling-api-verification.json'
api=json.loads((ROOT/path).read_text(encoding='utf-8'));assert api['passed'] and api['pure_gpu_path_verified']
assert api['total']==99208302 and api['original_total']==95753434 and api['delta']==3454868
members={'목단':29079198,'크라운':9834353,'앨리스':28397499,'모더니아':25043505,'리타':6853747};assert sum(members.values())==api['total']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();assert all(sha(p)==h for p,h in api['source_sha256'].items())
files=set(api['source_sha256'])|{path,'research/detail-survival-scaling-ui-fixture.json','research/record-survival-scaling-browser-proof.py'}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,browser_interaction_verified=True,browser='Codex In-app Browser',url='http://127.0.0.1:4332/#results',fictional_owned_data=True,live_account_import_verified=False,restored_owned_characters=5,temporary_stat_deltas={'목단':dict(atk=12000,hp=100000,**{'def':250})},observed_skills=[7,5,9],observed_cube='렐릭 베어 큐브',observed_cube_level=4,total=api['total'],original_total=api['original_total'],delta=api['delta'],members=members,CPU_verified_UI=True,pure_GPU_UI=True,source_sha256={p:sha(p) for p in sorted(files)})
(ROOT/'research/detail-survival-scaling-browser-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded observed UI acceptance; full all-effects goal incomplete.')
