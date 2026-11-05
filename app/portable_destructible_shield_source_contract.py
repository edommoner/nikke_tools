"""Exact provider refactor inverse for immutable projectile captures only."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_destructible_hit_shield_source_contract import project_sources as project_hit
    root=Path(root);sources=project_hit(root,sources)
    data=json.loads((root/'tests/fixtures/portable-destructible-shield-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed shield Frame provider source: '+name
        old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources

def verify_retained_sources(root,source,expected):
    from portable_attack_group_source_contract import retained_source_hashes
    actual=retained_source_hashes(root,source)
    for name,text in project_sources(root).items():
        if name in actual:
            if name=='gpu/quantity_runtime.slang':
                from portable_quantity_visited_source_contract import historical_source
                text=historical_source(root,text)
            actual[name]=hashlib.sha256(text.encode()).hexdigest()
    assert actual==expected,'Retained source differs beyond exact shield provider refactor'
