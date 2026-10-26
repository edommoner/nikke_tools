"""Exact reviewed coordinate receipt delta before retained source ledgers.

No token/regex exclusions: verify both full hashes and unique literal changes.
Numerical parity remains the independently sealed Metal proof, not this audit.
"""
import hashlib,json
from pathlib import Path


def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-coordinate-full-burst-source-delta.json').read_text())


def project_sources(root,sources=None):
    from portable_coordinate_generation_source_contract import project_sources as project_generations
    root=Path(root);sources=project_generations(root,sources);data=ledger(root)
    for name in data['sources']:sources[name]=project_file(root,name,sources.get(name,(root/name).read_text()))
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed coordinate full-burst entry: '+name
    return sources


def project_file(root,name,current=None):
    """Use one exact reviewed receipt delta when other files are already older."""
    root=Path(root);row=ledger(root)['sources'][name]
    current=(root/name).read_text() if current is None else current
    assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate full-burst source: '+name
    for change in reversed(row['changes']):
        assert change['current'] and current.count(change['current'])==1,'Missing or ambiguous coordinate delta: '+name
        current=current.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(current.encode()).hexdigest()==row['baseline_sha256'],'Coordinate historical source changed: '+name
    return current
