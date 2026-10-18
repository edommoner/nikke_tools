"""Seal the passing common cases and the independently demonstrated collision."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=['research/detail-hp-edge-staged-native.json','research/detail-hp-edge-staged-ptx.json','research/detail-hp-edge-staged-real-native.json','research/detail-hp-edge-before-namespace-fix.json']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();paths=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'))
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),path
    if path.endswith('before-namespace-fix.json'):assert not r['passed'] and sum(not x['passed'] for x in r['cases'])==2
    elif '-real-' not in path:assert r['passed'] and len(r['cases'])==24
    paths.update(r['source_sha256'])
paths.update(['research/detail-hp-edge-staged-native.log','research/detail-hp-edge-staged-ptx.log','research/detail-hp-edge-staged-real-native.log','research/detail-hp-edge-before-namespace-fix.log','research/staging/v35/scripts/build-combat.py','research/staging/v35/scripts/build-detail-native.py','research/staging/v35/stage-base.json','research/archive-hp-edge-before-namespace-fix.py'])
dest=ROOT/'research/ports/v35-before-self-event-namespace-fix';assert not dest.exists(),'Archives are immutable.'
for p in sorted(paths):
    source,target=(ROOT/p).resolve(),(dest/p).resolve();assert source.is_relative_to(ROOT) and target.is_relative_to(dest)
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
(dest/'archive-manifest.json').write_text(json.dumps(dict(stage_only=True,objective_complete=False,known_failure='Self HP and same-text generic named events collide.',files={p:sha(p) for p in sorted(paths)}),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(archived=str(dest),files=len(paths),objective_complete=False)))
