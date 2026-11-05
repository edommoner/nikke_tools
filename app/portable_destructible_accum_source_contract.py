"""Exact HSI6 source delta for prior proofs; not generated-code normalization."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_attack_group_source_contract import project_sources as attack_group_sources
    root=Path(root);sources=attack_group_sources(root,sources)
    for name,row in json.loads((root/'tests/fixtures/portable-destructible-accum-source-delta.json').read_text())['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed body-accumulation source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];sources[name]=row['baseline']
    return sources
def verify_retained_sources(root,source,expected):
    from portable_attack_group_source_contract import retained_source_hashes
    actual=retained_source_hashes(root,source)
    for name,value in project_sources(root).items():
        if name in actual:
            if name=='gpu/quantity_runtime.slang':
                from portable_quantity_visited_source_contract import historical_source
                value=historical_source(root,value)
            actual[name]=hashlib.sha256(value.encode()).hexdigest()
    assert actual==expected,'Unexpected source outside exact HSI6 delta'
