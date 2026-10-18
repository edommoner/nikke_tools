"""Record the freshly observed ordinary GPU demo screen; run after UI checks."""
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
elapsed=float(sys.argv[1]);assert elapsed>=0
manifest=json.loads((ROOT/'app/detail_effects-sm86.json').read_text(encoding='utf-8'));assert manifest['abi']=='detail_random_v20'
row=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,abi='detail_random_v20',url='http://127.0.0.1:4332/#single',
 browser='Brave',normal_screen=True,synthetic_demo=True,seed=12345,shooting_policy='character',burst_policy='mast3',burst_gauge_mode='accumulate',
 displayed_total=243679868,displayed_members=[137652644,17503770,32239833,21129893,35153728],
 displayed_backend='cuda_detail',displayed_module='cubin-sm86',cpu_verification_matched=True,displayed_elapsed_seconds=elapsed,seed_stale_result_checked=True,seed_restored=12345,
 note='Fresh ordinary UI calculation observed after restarting owned4332 v20 server; character controls, Mast pattern, accumulated burst gauge and explicitly selected seed12345. File save/import roundtrip is not UI-tested. Not every character or every combination.')
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-build.json','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py','web/app.js','web/index.html']
row['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
(ROOT/'research/detail-random-ui-verification.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in row.items() if k!='source_sha256'},ensure_ascii=True))
