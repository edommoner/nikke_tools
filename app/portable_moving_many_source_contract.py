"""Exact inverse of the wide observation banks; no generated-code exclusions."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
from portable_removed_sources import REMOVED_SOURCES
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    root=Path(root);out=dict(sources or {})
    if (root/'gpu/world_coordinate_typed_ordered_history_entry.slang').exists():
        from portable_recipient_order_source_contract import project_sources as recipient_order
        out=recipient_order(root,out)
    ledger=json.loads((root/'tests/fixtures/portable-moving-many-source-delta.json').read_text())
    older=[json.loads((root/'tests/fixtures'/name).read_text())['files'] for name in ('portable-moving-typed-source-delta.json','portable-enemy-movement-source-delta.json')]
    digest=lambda value:hashlib.sha256(value.encode()).hexdigest()
    for name,expected in ledger['added_sources'].items():
        if name in REMOVED_SOURCES:continue
        if digest(out.get(name,cpu_only_text(root,name,(root/name).read_text())))!=expected:raise ValueError('Unreviewed maximum-slot dependency: '+name)
    for name,row in ledger['files'].items():
        if name in REMOVED_SOURCES:continue
        value=out.get(name,cpu_only_text(root,name,(root/name).read_text()));sha=digest(value)
        allowed={row['before_sha256'],*[old.get(name,{}).get('before_sha256') for old in older]}
        if name in out and sha in allowed:continue
        if sha!=row['after_sha256']:raise ValueError('Unreviewed maximum-slot source: '+name)
        for h in reversed(row['hunks']):
            if value.count(h['after'])!=1:raise ValueError('Ambiguous maximum-slot inverse')
            value=value.replace(h['after'],h['before'],1)
        if digest(value)!=row['before_sha256']:raise ValueError('Maximum-slot inverse differs')
        out[name]=value
    return out
