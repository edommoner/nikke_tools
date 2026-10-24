"""Exact HSI6 source delta for prior proofs; not generated-code normalization."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {})
    for name,row in json.loads((root/'tests/fixtures/portable-destructible-accum-source-delta.json').read_text())['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed body-accumulation source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];sources[name]=row['baseline']
    return sources
def verify_retained_sources(root,source,expected):
    from portable_backend import source_hashes
    actual=source_hashes(source)
    for name,value in project_sources(root).items():
        if name in actual:actual[name]=hashlib.sha256(value.encode()).hexdigest()
    assert actual==expected,'Unexpected source outside exact HSI6 delta'
