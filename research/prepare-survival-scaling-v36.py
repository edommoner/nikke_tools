"""Isolate the next survival-effects ABI from accepted ordinary production v35."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'research/staging/v36'
c=json.loads((ROOT/'research/detail-hp-edge-checkpoint.json').read_text(encoding='utf-8'))
assert c['passed'] and c['abi']=='detail_hp_edge_v35' and not c['objective_complete']
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in c['source_sha256'].items())
assert not dest.exists(),'Do not reset an existing survival-scaling port.'
for path in ['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']:
    s=(ROOT/path).read_text(encoding='utf-8').replace('detail_hp_edge_v35','detail_survival_scaling_v36').replace('detail_state_bytes_v35','detail_state_bytes_v36').replace('detail_boss_shape_v35','detail_boss_shape_v36')
    p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
(dest/'stage-base.json').write_text(json.dumps(dict(base_abi=c['abi'],base_checkpoint_sha256=hashlib.sha256((ROOT/'research/detail-hp-edge-checkpoint.json').read_bytes()).hexdigest(),objective_complete=False,stage_verified=False),indent=2)+'\n',encoding='utf-8')
print('Created v36 stage; production v35 stays unchanged.')
