import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
row=json.loads((ROOT/'research/detail-burst-gauge-ui-verification.json').read_text(encoding='utf-8'))
row.update(generated_at=datetime.now(timezone.utc).isoformat(),abi='detail_burst_stage_v18',displayed_elapsed_seconds=8.10)
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-build.json','app/detail_effects-sm86.json','app/engine_worker.py','web/app.js','web/index.html']
row['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
(ROOT/'research/detail-burst-stage-ui-verification.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
