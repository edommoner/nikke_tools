"""Preserve boundary-test setup failure before correcting its world input."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p='research/detail-cover-capacity-boundary-verification.json';r=json.loads((ROOT/p).read_text(encoding='utf-8'));assert not r['passed'] and not r['gpu_run']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();assert all(sha(f)==h for f,h in r['source_sha256'].items())
files=set(r['source_sha256'])|{p,'research/detail-cover-capacity-boundary-tests.log','research/archive-cover-capacity-boundary-initial.py'}
dest=ROOT/'research/ports/v37-boundary-initial';assert not dest.exists()
for f in sorted(files):
    out=(dest/f).resolve();assert out.is_relative_to(dest.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,out)
(dest/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,gpu_run=False,reason='Boundary-only setup included a live boss but used a unit script; expected marker validation was not reached.',files={f:sha(f) for f in sorted(files)}),indent=2)+'\n',encoding='utf-8')
