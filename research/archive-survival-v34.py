"""Preserve the final production v34 closure before another GPU ABI change."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checkpoint = 'research/detail-survival-checkpoint.json'
c = json.loads((ROOT / checkpoint).read_text(encoding='utf-8'))
assert c['passed'] and not c['objective_complete'] and c['abi'] == 'detail_survival_v34'
sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
for field in ('source_sha256', 'report_sha256'):
    assert all(sha(p) == h for p, h in c[field].items()), field
paths = set(c['source_sha256']) | set(c['report_sha256']) | {
    checkpoint, 'research/detail-expansion-next.json',
    'scripts/build-combat.py', 'scripts/build-detail-native.py',
    'research/detail-survival-final-normal-tests.log',
    'research/detail-survival-final-api-verification.log',
    'research/detail-survival-node-tests.log',
    'research/archive-survival-v34.py',
}
for report in c['reports']:
    r = json.loads((ROOT / report).read_text(encoding='utf-8'))
    assert r['passed']
    assert all(sha(p) == h for p, h in r['source_sha256'].items()), report
    paths.update(r['source_sha256'])
stage = ROOT / c['staging_archive']
m = json.loads((stage / 'archive-manifest.json').read_text(encoding='utf-8'))
for p, h in m['files'].items():
    source = (stage / p).resolve()
    assert source.is_relative_to(stage.resolve())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == h
    paths.add(str(source.relative_to(ROOT)).replace('\\', '/'))
dest = ROOT / 'research/ports/v34-final'
assert not dest.exists(), 'Preserved archives are immutable.'
for p in sorted(paths):
    source, target = (ROOT / p).resolve(), (dest / p).resolve()
    assert source.is_relative_to(ROOT) and target.is_relative_to(dest)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
(dest / 'archive-manifest.json').write_text(json.dumps(dict(
    abi=c['abi'], objective_complete=False,
    files={p: sha(p) for p in sorted(paths)},
), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(archived=str(dest), files=len(paths), objective_complete=False)))
