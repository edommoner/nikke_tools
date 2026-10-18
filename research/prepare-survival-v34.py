"""Create an isolated next-ABI source stage; the verified v33 app stays usable."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'research/staging/v34'
c=json.loads((ROOT/'research/detail-incoming-checkpoint.json').read_text(encoding='utf-8'))
assert c['passed'] and c['abi']=='detail_incoming_v33' and not c['objective_complete']
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in c['source_sha256'].items())
assert not dest.exists(),'Do not reset existing survival work.'
paths=['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']
for path in paths:
 text=(ROOT/path).read_text(encoding='utf-8').replace('detail_incoming_v33','detail_survival_v34').replace('detail_state_bytes_v33','detail_state_bytes_v34').replace('detail_boss_shape_v33','detail_boss_shape_v34')
 p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
(dest/'stage-base.json').write_text(json.dumps(dict(base_abi=c['abi'],base_source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},objective_complete=False,stage_verified=False,notes='Only staged detail_gpu is substituted into sys.modules by the development verifier. Other app modules and pinned CPU remain at the original workspace.'),indent=2)+'\n',encoding='utf-8')
print('Created isolated v34 source stage; production files and v33 binaries unchanged.')
