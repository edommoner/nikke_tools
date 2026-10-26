"""Exact reviewed delta for historical fixtures; never numerical normalization."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_destructible_lifesteal_source_contract import project_sources as lifesteal_sources
    root=Path(root);sources=lifesteal_sources(root,sources)
    data=json.loads((root/'tests/fixtures/portable-destructible-roster-skill-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed roster skill source: '+name
        old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources

def verify_retained_sources(root,source,expected):
    from portable_attack_group_source_contract import retained_source_hashes
    actual=retained_source_hashes(root,source)
    projected=project_sources(root)
    # This older typed fixture predates only the coordinate receipt copy in
    # this file. Other coordinate files have already reached older ledgers.
    from portable_coordinate_full_burst_source_contract import project_file
    name='gpu/full_burst_landing_runtime.slang'
    if name not in projected:projected[name]=project_file(root,name)
    for name,text in projected.items():
        if name in actual:actual[name]=hashlib.sha256(text.encode()).hexdigest()
    assert actual==expected,'Retained source differs beyond exact roster-skill delta'
