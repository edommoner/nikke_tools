"""Exact historical source projection; never a generated-code normalizer."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root)
    ledger=json.loads((root/'tests/fixtures/portable-logical-geometry-source-delta.json').read_text())
    projected=dict(sources or {})
    if (root/'gpu/world_enemy_healing_entry.slang').exists():
        from portable_enemy_healing_source_contract import project_sources as healing
        # Keep every checked inverse for earlier contracts (including the
        # named-enemy/stack composition). Dropping those dependencies makes
        # an older caller reload current source in the middle of its inverse.
        projected=healing(root,projected)
    for name,digest in ledger['added_sources'].items():
        source=projected.get(name,(root/name).read_text())
        if hashlib.sha256(source.encode()).hexdigest()!=digest:raise ValueError('Logical geometry dependency changed: '+name)
    for name,record in ledger['files'].items():
        source=projected.get(name,(root/name).read_text())
        if name in projected and hashlib.sha256(source.encode()).hexdigest()==record['before_sha256']:continue
        if hashlib.sha256(source.encode()).hexdigest()!=record['after_sha256']:raise ValueError('Logical geometry source changed: '+name)
        for change in reversed(record['changes']):
            if source.count(change['after'])!=1:raise ValueError('Ambiguous logical geometry inverse: '+name)
            source=source.replace(change['after'],change['before'],1)
        if hashlib.sha256(source.encode()).hexdigest()!=record['before_sha256']:raise ValueError('Historical source projection differs: '+name)
        projected[name]=source
    tail=(root/'gpu/coordinate_group_actor_receipt.slang').read_text()
    record=ledger['files']['gpu/coordinate_physical_runtime.slang']['changes'][0]
    if tail!=record['before']+'\n':raise ValueError('Shared actor receipt is not the exact prior landing tail')
    return projected

def project_backend_source(root,source=None):
    root=Path(root);name='app/portable_backend.py'
    return project_sources(root,{name:(root/name).read_text() if source is None else source})[name]
