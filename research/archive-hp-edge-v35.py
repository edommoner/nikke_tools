"""Preserve the production v35 closure before the next GPU effect port."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];checkpoint='research/detail-hp-edge-checkpoint.json'
c=json.loads((ROOT/checkpoint).read_text(encoding='utf-8'));assert c['passed'] and not c['objective_complete'] and c['abi']=='detail_hp_edge_v35'
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
for field in ('source_sha256','report_sha256'):assert all(sha(p)==h for p,h in c[field].items()),field
paths=set(c['source_sha256'])|set(c['report_sha256'])|{checkpoint,'research/detail-expansion-next.json','research/archive-hp-edge-v35.py','research/detail-hp-edge-normal-tests.log','research/detail-hp-edge-api-verification.log','research/detail-lost-hp-cpu-reference.log','research/detail-cover-revival-cpu-reference.log'}
stage=ROOT/c['staging_archive'];manifest=json.loads((stage/'archive-manifest.json').read_text(encoding='utf-8'))
for p,h in manifest['files'].items():
    source=(stage/p).resolve();assert source.is_relative_to(stage)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==h
    paths.add(str(source.relative_to(ROOT)).replace('\\','/'))
dest=ROOT/'research/ports/v35-final';assert not dest.exists(),'Preserved archives are immutable.'
for p in sorted(paths):
    source,target=(ROOT/p).resolve(),(dest/p).resolve();assert source.is_relative_to(ROOT) and target.is_relative_to(dest)
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
(dest/'archive-manifest.json').write_text(json.dumps(dict(abi=c['abi'],objective_complete=False,files={p:sha(p) for p in sorted(paths)}),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(archived=str(dest),files=len(paths),objective_complete=False)))
