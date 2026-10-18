"""Record the rendered UI evidence observed through cua_repl, not hidden state.

The download listener stalled; no successful session export is claimed here.
Structured CPU verification is independently exercised by the API smoke report.
"""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_boss.py','app/detail_world.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py','server.mjs','web/app.js','web/phase-model.mjs','web/style.css','research/save-boss-clock-ui-evidence.py']
members=[('モダニア',151791008),('ルージュ',19755284),('マスト：ロマンチックメイド',33990505),('ドラー',23296910),('マクスウェル',39977128)]
assert sum(d for n,d in members)==268810835
events=[(3,'core','start'),(3,'move','start'),(8,'core','expired'),(8,'move','expired'),(11,'core','start'),(16,'core','expired'),(19,'core','start'),(24,'core','expired'),(27,'core','start'),(32,'core','expired'),(35,'core','start'),(40,'core','expired'),(43,'core','start'),(48,'core','expired'),(51,'core','start'),(56,'core','expired'),(59,'core','start'),(60,'core','end')]
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,provenance='Observed normal UI: Brave tab 71557270, #single-result innerText, expanded boss timeline. No hidden page state or CPU trace supplied to GPU.',url='http://127.0.0.1:4332/#single',fictional_demo_profile=True,backend='cuda_detail',backend_evidence='GPU詳細計算 · NVIDIA GeForce RTX 3070 Ti',cpu_verification={'total_equal':True,'members_equal':True,'burst_timeline_equal':True,'base_stats_equal':True},cpu_verification_evidence='CPU照合済み（部隊合計・5人のダメージ・バースト時刻・基礎ステータス一致）',total=268810835,baseline=267515135,difference=1295700,members=[dict(name=n,damage=d) for n,d in members],duration=60,shooting_policy='character',burst_policy='mast3',burst_gauge_mode='accumulate',seed=0,delta_applied=True,delta={'character':'モダニア','atk':1000},boss_events=len(events),boss_timeline_observed=events,preset_saved='GPU照合用・コア周期と距離',session_export_verified=False,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-boss-clock-ui-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'total':r['total'],'boss_events':r['boss_events'],'evidence':'rendered UI'}))
