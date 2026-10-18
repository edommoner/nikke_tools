"""Isolate received-healing accumulation against accepted production v41."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];cp=ROOT/'research/detail-heal-sharing-checkpoint.json';r=json.loads(cp.read_text(encoding='utf-8'))
assert r['passed'] and r['abi']=='detail_heal_sharing_v41'
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in r['source_sha256'].items())
stage=ROOT/'research/staging/v42';assert not stage.exists(),'Never overwrite a port.'
for name in ['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']:
    s=(ROOT/name).read_text(encoding='utf-8').replace('detail_heal_sharing_v41','detail_heal_charge_v42').replace('detail_state_bytes_v41','detail_state_bytes_v42').replace('detail_boss_shape_v41','detail_boss_shape_v42')
    out=stage/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(s,encoding='utf-8')
(stage/'stage-base.json').write_text(json.dumps(dict(base_abi=r['abi'],base_checkpoint_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),objective_complete=False,stage_verified=False),indent=2)+'\n',encoding='utf-8')
print('Isolated v42 created. Accepted v41 production unchanged.')
