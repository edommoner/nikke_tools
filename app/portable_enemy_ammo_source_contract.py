"""Exact inverse of enemy ammo hooks and shared numeric extraction."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    root=Path(root);ledger=json.loads((root/'tests/fixtures/portable-enemy-ammo-source-delta.json').read_text());out=dict(sources or {})
    from portable_enemy_ammo_combined_source_contract import project_resident_scalars
    out=project_resident_scalars(root,out)
    if (root/'gpu/world_add_self_destruct_entry.slang').exists():
        from portable_add_self_destruct_source_contract import project_sources as self_destruct
        out=self_destruct(root,out)
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise ValueError('Unreviewed enemy ammo dependency: '+name)
    for name,row in ledger['files'].items():
        current=out.get(name,(root/name).read_text());digest=hashlib.sha256(current.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if current!=row['after'] or digest!=row['after_sha256'] or hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:raise ValueError('Unreviewed enemy ammo shared source: '+name)
        out[name]=row['before']
    return out
