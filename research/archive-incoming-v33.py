"""Preserve the verified v33 source/report closure before the next ABI port."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];checkpoint='research/detail-incoming-checkpoint.json'
c=json.loads((ROOT/checkpoint).read_text(encoding='utf-8'));assert c['passed'] and not c['objective_complete'] and c['abi']=='detail_incoming_v33'
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert all(sha(p)==h for p,h in c['source_sha256'].items()) and all(sha(p)==h for p,h in c['report_sha256'].items())
paths=set(c['source_sha256'])|set(c['report_sha256'])|{checkpoint,'research/detail-expansion-next.json','scripts/build-combat.py','scripts/build-detail-native.py','research/detail-incoming-api-sandbox-failure.log','research/detail-incoming-native-verification.log','research/detail-incoming-ptx-verification.log','research/detail-incoming-normal-tests.log'}
for path in c['reports']:
 r=json.loads((ROOT/path).read_text(encoding='utf-8'));paths.update(r['source_sha256'])
dest=ROOT/'research/ports/v33';assert not dest.exists(),'Preserved archives are immutable.'
for p in sorted(paths):
 source=(ROOT/p).resolve();target=(dest/p).resolve();assert source.is_relative_to(ROOT.resolve()) and target.is_relative_to(dest.resolve())
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
(dest/'archive-manifest.json').write_text(json.dumps(dict(abi=c['abi'],objective_complete=False,files={p:sha(p) for p in sorted(paths)}),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(archived=str(dest),files=len(paths),objective_complete=False)))
