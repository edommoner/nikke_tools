"""Exact inverse for shared final-queue GPU hooks; no golden normalization."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {})
    out=project_resident_scalars(root,out)
    ledger=json.loads((root/'tests/fixtures/portable-enemy-ammo-combined-source-delta.json').read_text(encoding='utf-8'))
    for name,digest in ledger['added_sources'].items():
        value=out[name] if name in out else (root/name).read_text(encoding='utf-8')
        if hashlib.sha256(value.encode()).hexdigest()!=digest:raise ValueError('Unreviewed combined magazine dependency: '+name)
    for name,row in ledger['files'].items():
        value=out[name] if name in out else (root/name).read_text(encoding='utf-8');digest=hashlib.sha256(value.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if value!=row['after'] or digest!=row['after_sha256'] or hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:
            raise ValueError('Unreviewed combined magazine shared source: '+name)
        out[name]=row['before']
    return out


def project_resident_scalars(root,sources=None):
    root=Path(root);out=dict(sources or {})
    if (root/'gpu/world_moving_typed_entry.slang').exists():
        from portable_moving_typed_source_contract import project_sources as moving_typed
        out=moving_typed(root,out)
    if (root/'gpu/world_enemy_movement_entry.slang').exists():
        from portable_enemy_movement_source_contract import project_sources as movement
        out=movement(root,out)
    snapshot=root/'tests/fixtures/portable-healing-hp-snapshot-delta.json'
    if snapshot.exists():
        for name,delta in json.loads(snapshot.read_text())['files'].items():
            value=out[name] if name in out else (root/name).read_text()
            # An outer caller may already have applied this exact inverse.
            if not (name in out and hashlib.sha256(value.encode()).hexdigest()==delta['baseline_sha256']):
                if hashlib.sha256(value.encode()).hexdigest()!=delta['current_sha256']:raise ValueError('Unreviewed resident scalar snapshot source')
                for change in reversed(delta['changes']):
                    if value.count(change['current'])!=1:raise ValueError('Ambiguous resident scalar snapshot inverse')
                    value=value.replace(change['current'],change['baseline'],1)
                if hashlib.sha256(value.encode()).hexdigest()!=delta['baseline_sha256']:raise ValueError('Resident scalar snapshot historical source changed')
                out[name]=value
    return out
