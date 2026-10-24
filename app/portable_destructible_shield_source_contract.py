"""Exact provider refactor inverse for immutable projectile captures only."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {})
    data=json.loads((root/'tests/fixtures/portable-destructible-shield-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed shield Frame provider source: '+name
        old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources

def verify_retained_sources(root,source,expected):
    from portable_backend import source_hashes
    actual=source_hashes(source)
    for name,text in project_sources(root).items():
        if name in actual:actual[name]=hashlib.sha256(text.encode()).hexdigest()
    assert actual==expected,'Retained source differs beyond exact shield provider refactor'
