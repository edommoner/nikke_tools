"""Archive the verified v30 implementation before the live-world port."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_world.py','app/engine_worker.py','app/gpu_service.py','scripts/build-combat.py','scripts/build-detail-native.py','scripts/verify-normal-detail.py','research/detail-normal-acceptance.json','research/detail-named-capacity-checkpoint.json','server.mjs','web/app.js','web/index.html','web/style.css','web/enemy-model.mjs']
for name in files:
    dst=ROOT/'research/ports/v30'/name
    assert not dst.exists(),dst
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
print('Archived v30')
