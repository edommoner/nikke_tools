"""Exact target-name landing delta; preserve the prior full-burst ledger."""
import hashlib,json
from pathlib import Path


def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-coordinate-generation-source-delta.json').read_text())


def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    root=Path(root);sources=dict(sources or {})
    for name,row in ledger(root)['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate generation source: '+name
        for change in reversed(row['changes']):
            assert change['current'] and current.count(change['current'])==1,'Missing or ambiguous generation delta: '+name
            current=current.replace(change['current'],change['baseline'],1)
        assert hashlib.sha256(current.encode()).hexdigest()==row['baseline_sha256'],'Generation historical source changed: '+name
        sources[name]=current
    return sources
