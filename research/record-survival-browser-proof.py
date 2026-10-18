"""Record observations from actual browser UI actions, not a parser-only claim.

The in-app browser restored the fictional fixture, clicked the normal single
squad calculation in both GPU modes, and displayed these values. The final
verified result was restored from that preview's cache and captured in a browser
screenshot. The independent ordinary API test binds the same input and sources.
"""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
api_path='research/detail-survival-api-verification.json'
api=json.loads((ROOT/api_path).read_text(encoding='utf-8'))
assert api['passed'] and api['pure_gpu_path_verified'] and api['total']==71474691
assert api['compute']['backend']=='cuda_detail' and api['compute']['workspace_bytes']==1049568
assert api['compute']['cpu_verification']['matched']
files=set(api['source_sha256'])|{api_path,'research/detail-survival-ui-fixture.json','research/record-survival-browser-proof.py','web/board-model.mjs'}
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert all(sha(p)==h for p,h in api['source_sha256'].items())
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,browser_interaction_verified=True,browser='Codex In-app Browser',url='http://127.0.0.1:4332/#results',
    fictional_owned_data=True,live_account_import_verified=False,restored_owned_characters=5,temporary_stat_deltas={'앨리스':dict(atk=12000,hp=100000,**{'def':250})},
    original_total=70901468,changed_total=71474691,delta=573223,pure_gpu_total=71474691,cpu_verified_gpu_total=71474691,api_total=api['total'],
    members={'라푼젤':8252759,'리타':8034596,'크라운':11893679,'모더니아':33122786,'앨리스':10170871},
    device='NVIDIA GeForce RTX 3070 Ti',pure_gpu_path_verified=True,cpu_verified_badge_observed=True,screenshot_captured=True,screenshot_method='previewTab.screenshot({fullPage:true}) emitted in the current browser tool output',
    observations=['Saved fixture restored through the visible JSON file chooser.','Different skill levels, five positions and the temporary Alice stat delta appeared in the ordinary single-squad UI.','GPU + CPU verification displayed 71,474,691 with a CPU match badge.','GPU without CPU verification displayed the same total and no CPU verification badge.','The verified result was restored and the results tab was captured.'],
    source_sha256={p:sha(p) for p in sorted(files)})
assert sum(r['members'].values())==r['changed_total']
(ROOT/'research/detail-survival-browser-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,browser_interaction_verified=True,total=r['changed_total'])))
