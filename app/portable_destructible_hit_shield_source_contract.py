"""Exact opt-in hit-credit delta; never changes historical source evidence."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_destructible_weapon_source_contract import project_sources as project_weapon
    root=Path(root);sources=project_weapon(root,sources)
    data=json.loads((root/'tests/fixtures/portable-destructible-hit-shield-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed hit-shield policy source: '+name
        old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources

def verify_retained_sources(root,source,expected):
    from portable_backend import source_hashes
    actual=source_hashes(source)
    for name,text in project_sources(root).items():
        if name in actual:actual[name]=hashlib.sha256(text.encode()).hexdigest()
    assert actual==expected,'Retained source differs beyond exact hit-shield delta'
