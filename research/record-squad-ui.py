"""Record the freshly observed 203-character demo edited through normal UI."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py','server.mjs','web/app.js','web/index.html']
row=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,feature='v21 squad affiliation condition',abi='detail_random_v20',url='http://127.0.0.1:4332/#single',browser='Brave',normal_screen=True,synthetic_demo=True,
 displayed_total=506845264,displayed_members=[64780828,31443004,60967075,104439944,245214413],squad=['누아르','루주','크라운','앨리스','모더니아'],seed=12345,duration=60,shooting_policy='character',burst_policy='rules',burst_gauge_mode='accumulate',
 displayed_backend='cuda_detail',displayed_module='cubin-sm86',cpu_verification=dict(total_equal=True,members_equal=True,burst_timeline_equal=True,base_stats_equal=True,seed_equal=True,matched=True),displayed_elapsed_seconds=21.15,workspace_bytes=256912,
 noir_burst_times=[3.98,33.28],note='Owned v21 server10754 on4332; expanded203 synthetic demo, edited five slots through UI controls. Full raw skills retained; real Noir/Rouge affiliation and two Noir burst casts observed. File upload not needed or UI-tested. Not every character/favorite/combination.')
assert sum(row['displayed_members'])==row['displayed_total']
row['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
(ROOT/'research/detail-squad-ui-verification.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in row.items() if k!='source_sha256'},ensure_ascii=True))
