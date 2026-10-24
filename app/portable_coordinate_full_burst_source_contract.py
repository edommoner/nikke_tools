"""Exact reviewed coordinate receipt delta before retained source ledgers.

No token/regex exclusions: verify both full hashes and unique literal changes.
Numerical parity remains the independently sealed Metal proof, not this audit.
"""
import hashlib,json
from pathlib import Path


def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-coordinate-full-burst-source-delta.json').read_text())


def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {});data=ledger(root)
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate full-burst source: '+name
        for change in reversed(row['changes']):
            assert change['current'] and current.count(change['current'])==1,'Missing or ambiguous coordinate delta: '+name
            current=current.replace(change['current'],change['baseline'],1)
        assert hashlib.sha256(current.encode()).hexdigest()==row['baseline_sha256'],'Coordinate historical source changed: '+name
        sources[name]=current
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed coordinate full-burst entry: '+name
    return sources
