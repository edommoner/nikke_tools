"""Seal real-squad successes and the independent per-frame synthetic failures."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=['research/detail-survival-scaling-authored-native.json','research/detail-survival-scaling-authored-ptx.json','research/detail-survival-scaling-cover-native-probe.json','research/detail-survival-scaling-real-native-probe.json']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();paths=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert all(sha(p)==h for p,h in r['source_sha256'].items()),path
    paths.update(r['source_sha256'])
assert json.loads((ROOT/reports[-1]).read_text(encoding='utf-8'))['passed']
paths.update(['research/archive-scaling-before-HP-unit-fix.py','research/detail-survival-scaling-authored-native.log','research/detail-survival-scaling-authored-ptx.log','research/detail-survival-scaling-cover-native-probe.log','research/detail-survival-scaling-real-native-probe.log'])
dest=ROOT/'research/ports/v36-before-HP-unit-and-cover-value-fix';assert not dest.exists()
for p in sorted(paths):
    source,target=(ROOT/p).resolve(),(dest/p).resolve();assert source.is_relative_to(ROOT) and target.is_relative_to(dest)
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
(dest/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_survival_scaling_v36',objective_complete=False,gpu_verified=False,known_failures=['Lost-HP scaled max-HP activation must still divide the full value by the active stack (pinned CPU rule).','cover_revive handler consumes the supplied base percent and ignores scaling_ref, unlike generic value().','Cover repeat-revival fixture incorrectly required a character revival because its name ends with revival.'],files={p:sha(p) for p in sorted(paths)}),indent=2)+'\n',encoding='utf-8')
print('Preserved pre-fix candidate, 12 passing actual native squads, both failed frame matrices and the test witness error.')
