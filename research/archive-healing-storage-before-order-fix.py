"""Preserve passed math parity before correcting the newly modeled burst order."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=[f'research/detail-healing-storage-{k}-{b}.json' for k in ('authored','extra','real','regression') for b in ('native','ptx')]+['research/detail-healing-storage-cpu-reference.json','research/detail-healing-storage-cpu-squads.json','research/detail-healing-storage-cpu-legacy.json','research/detail-healing-storage-boundary-verification.json'];files=set(reports)|{'research/archive-healing-storage-before-order-fix.py'}
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'] and all(sha(p)==h for p,h in r['source_sha256'].items()),path;files.update(r['source_sha256'])
dest=ROOT/'research/ports/v40-before-burst-order-fix';assert not dest.exists()
for path in sorted(files):
    out=(dest/path).resolve();assert out.is_relative_to(dest.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,out)
(dest/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,gpu_arithmetic_mismatch=False,cases_per_backend=153,issue='Pinned skill-slot order heals Marciana before enabling storage; adjust definitions so new storage is available for her same-cast S2 heal.',reference_url='https://wiki3.jp/nikke/page/3640',files={p:sha(p) for p in sorted(files)}),indent=2)+'\n',encoding='utf-8');print('Preserved initial native/PTX153 proofs before burst-order model correction.')
