"""Create an isolated port; accepted v40 production remains unchanged."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cp=ROOT/'research/detail-healing-storage-checkpoint.json'
c=json.loads(cp.read_text(encoding='utf-8'))
assert c['passed'] and c['abi']=='detail_healing_storage_v40'
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in c['source_sha256'].items())
dest=ROOT/'research/staging/v41'
assert not dest.exists(),'Never overwrite a port.'
for name in ['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']:
    source=(ROOT/name).read_text(encoding='utf-8').replace('detail_healing_storage_v40','detail_heal_sharing_v41').replace('detail_state_bytes_v40','detail_state_bytes_v41').replace('detail_boss_shape_v40','detail_boss_shape_v41')
    out=dest/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(source,encoding='utf-8')
(dest/'stage-base.json').write_text(json.dumps(dict(base_abi=c['abi'],base_checkpoint_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),objective_complete=False,stage_verified=False),indent=2)+'\n',encoding='utf-8')
print('Isolated v41 created; v40 production unchanged.')
