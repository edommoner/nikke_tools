"""Exact private deferred-landing delta before all existing source proofs."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_full_burst_queue_source_contract import project_sources as project_queue
    root=Path(root);sources=project_queue(root,sources);data=json.loads((root/'tests/fixtures/portable-full-burst-landing-source-delta.json').read_text())
    for name,digest in data['added_sources'].items():assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed full-burst landing helper: '+name
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text());assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed full-burst landing source: '+name
        for change in reversed(row['changes']):
            assert current.count(change['current'])==1
            current=current.replace(change['current'],change['baseline'],1)
        assert hashlib.sha256(current.encode()).hexdigest()==row['baseline_sha256'];sources[name]=current
    return sources
