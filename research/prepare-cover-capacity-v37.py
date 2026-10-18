"""Isolate cover-capacity v37 from the accepted v36 production runtime."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'research/staging/v37'
p=ROOT/'research/detail-survival-scaling-checkpoint.json';c=json.loads(p.read_text(encoding='utf-8'))
assert c['passed'] and c['abi']=='detail_survival_scaling_v36'
assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in c['source_sha256'].items())
assert not dest.exists(),'Never reset an existing port.'
for path in ['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']:
    text=(ROOT/path).read_text(encoding='utf-8').replace('detail_survival_scaling_v36','detail_cover_capacity_v37').replace('detail_state_bytes_v36','detail_state_bytes_v37').replace('detail_boss_shape_v36','detail_boss_shape_v37')
    out=dest/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding='utf-8')
(dest/'stage-base.json').write_text(json.dumps(dict(base_abi=c['abi'],base_checkpoint_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),objective_complete=False,stage_verified=False),indent=2)+'\n',encoding='utf-8')
print('Created v37 stage; production v36 unchanged.')
