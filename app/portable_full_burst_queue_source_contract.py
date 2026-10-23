"""Exact live-queue/receipt ownership delta before the original landing proof."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_full_burst_capacity_source_contract import project_sources as project_capacity
    root=Path(root);sources=project_capacity(root,sources);data=json.loads((root/'tests/fixtures/portable-full-burst-queue-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed full-burst queue source: '+name
        assert current==row['current']
        old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources
