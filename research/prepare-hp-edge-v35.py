"""Isolate the HP-edge port while the accepted v34 app remains usable."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'research/staging/v35'
c=json.loads((ROOT/'research/detail-survival-checkpoint.json').read_text(encoding='utf-8'))
assert c['passed'] and c['abi']=='detail_survival_v34' and not c['objective_complete']
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in c['source_sha256'].items())
assert not dest.exists(), 'Do not reset an existing port.'
for path in ['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']:
    s=(ROOT/path).read_text(encoding='utf-8')
    for old in ('detail_survival_v34','detail_incoming_v33'):
        s=s.replace(old,'detail_hp_edge_v35')
    s=s.replace('detail_state_bytes_v34','detail_state_bytes_v35').replace('detail_boss_shape_v34','detail_boss_shape_v35')
    p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
(dest/'stage-base.json').write_text(json.dumps(dict(base_abi=c['abi'],base_checkpoint_sha256=hashlib.sha256((ROOT/'research/detail-survival-checkpoint.json').read_bytes()).hexdigest(),objective_complete=False,stage_verified=False),indent=2)+'\n',encoding='utf-8')
print('Created v35 stage; accepted production v34 remains unchanged.')
