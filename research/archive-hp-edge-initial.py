"""Preserve the initial no-notification-log candidate and its narrow proof."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];report='research/detail-hp-edge-initial-probe.json'
r=json.loads((ROOT/report).read_text(encoding='utf-8'));assert r['passed'] and not r['hp_notification_order_verified']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert all(sha(p)==h for p,h in r['source_sha256'].items())
paths=set(r['source_sha256'])|{report,'research/detail-hp-edge-initial-probe.log','research/detail-hp-edge-native-build.log','research/staging/v35/stage-base.json','research/archive-hp-edge-initial.py'}
dest=ROOT/'research/ports/v35-initial-no-notification-log';assert not dest.exists()
for p in paths:
    target=(dest/p).resolve();assert target.is_relative_to(dest.resolve());target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
(dest/'archive-manifest.json').write_text(json.dumps(dict(stage_only=True,objective_complete=False,hp_notification_order_verified=False,files={p:sha(p) for p in sorted(paths)}),indent=2)+'\n',encoding='utf-8')
print('Preserved initial eight-case native frame/damage proof; no notification-order claim.')
