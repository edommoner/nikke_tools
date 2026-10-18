"""Record actual ordinary UI actions observed through the in-app browser."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];api_path='research/detail-hp-edge-api-verification.json'
api=json.loads((ROOT/api_path).read_text(encoding='utf-8'))
assert api['passed'] and api['pure_gpu_path_verified'] and api['total']==194933444 and api['original_total']==197889526
assert api['compute']['backend']=='cuda_detail' and api['compute']['workspace_bytes']==1074184 and api['compute']['cpu_verification']['matched']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert all(sha(p)==h for p,h in api['source_sha256'].items())
members={'리타':32382811,'크라운':39705227,'A2':40086616,'앨리스':64982585,'N102':17776205};assert sum(members.values())==api['total']
files=set(api['source_sha256'])|{api_path,'research/detail-hp-edge-ui-fixture.json','research/record-hp-edge-browser-proof.py'}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,browser_interaction_verified=True,browser='Codex In-app Browser',url='http://127.0.0.1:4332/#results',
    fictional_owned_data=True,live_account_import_verified=False,restored_owned_characters=5,temporary_stat_deltas={'A2':dict(atk=12000,hp=100000,**{'def':250})},
    original_total=197889526,total=194933444,delta=-2956082,cpu_verified_gpu_total=194933444,pure_gpu_total=194933444,members=members,
    cpu_verified_badge_observed=True,pure_gpu_badge_has_no_cpu_verification=True,final_A2_hp_pct_observed=39.29926804331251,
    device='NVIDIA GeForce RTX 3070 Ti',verified_ui_gpu_ms=14572.064,pure_gpu_ui_seconds_displayed=15.86,speedup_claim=False,
    screenshot_captured=True,screenshot_method='previewTab.screenshot({fullPage:true}) emitted in the current browser tool output; no local path fabricated',
    observations=['Fictional session restored through the visible JSON file chooser.','Five positions and different skill levels, gear and temporary A2 changes restored in the single-squad UI.','The ordinary calculation button with GPU+CPU verification displayed 194,933,444, delta -2,956,082 and the CPU match badge.','The same ordinary button in pure GPU mode displayed the same total and members without the CPU match badge.','Returned to verified mode, recalculated the cached result, opened the results tab and captured a full-page screenshot.'],
    source_sha256={p:sha(p) for p in sorted(files)})
(ROOT/'research/detail-hp-edge-browser-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,total=r['total'],browser_interaction_verified=True,objective_complete=False)))
