"""Preserve the initial grammar and independently observed CPU revival failure."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'research/ports/v36-before-revival-scaling-context';assert not dest.exists()
files=['research/staging/v36/app/detail_gpu.py','research/staging/v36/app/detail_effects.cu','research/staging/v36/app/detail_effects.ptx','research/staging/v36/app/detail_effects-build.json','research/staging/v36/scripts/build-detail-native.py','research/staging/v36/scripts/build-combat.py','research/staging/v36/stage-base.json','scripts/staged-survival-scaling-runtime.py','research/probe-survival-scaling-cpu-readiness.py','research/detail-survival-scaling-cpu-readiness.json','app/survival_compat.py','research/archive-scaling-before-revival-context.py']
for p in files:
    target=(dest/p).resolve();assert target.is_relative_to(dest);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
(dest/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,gpu_verified=False,native_build_cancelled_for_required_source_change=True,known_CPU_failure='Moran and max-HP lost-HP scaling revival query None; no noncrashing CPU/GPU parity claim.',files={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}),indent=2)+'\n',encoding='utf-8')
print('Preserved pre-revival-context candidate, not GPU verified.')
