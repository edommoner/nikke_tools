"""Exact final deferred-state codec delta before the previous queue proof."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_full_burst_query_source_contract import project_sources as project_query
    root=Path(root);sources=project_query(root,sources);data=json.loads((root/'tests/fixtures/portable-full-burst-capacity-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed full-burst capacity source: '+name
        assert current==row['current'];old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources
