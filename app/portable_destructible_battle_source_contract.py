"""Exact latest opt-in delta; no historical source/hash is rewritten."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_destructible_coexist_source_contract import project_sources as project_coexist
    root=Path(root);sources=project_coexist(root,sources)
    data=json.loads((root/'tests/fixtures/portable-destructible-battle-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed destructible battle source: '+name
        old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources

def verify_retained_sources(root,source,expected):
    from portable_attack_group_source_contract import retained_source_hashes
    actual=retained_source_hashes(root,source)
    for name,text in project_sources(root).items():
        if name in actual:actual[name]=hashlib.sha256(text.encode()).hexdigest()
    assert actual==expected,'Retained source differs beyond the exact opt-in battle delta'
