"""Exact source inverse for opt-in enemy healing, never code normalization."""
import hashlib
import json
from pathlib import Path


def project_sources(root, sources=None):
    root = Path(root)
    ledger = json.loads((root/'tests/fixtures/portable-enemy-healing-source-delta.json').read_text())
    projected = dict(sources or {})
    if (root/'gpu/world_named_range_battle_entry.slang').exists():
        from portable_named_range_battle_source_contract import project_sources as radial
        projected=radial(root,projected)
    for name, digest in ledger['added_sources'].items():
        source = projected.get(name, (root/name).read_text())
        if hashlib.sha256(source.encode()).hexdigest() != digest:
            raise ValueError('Unreviewed enemy healing dependency: '+name)
    for name, row in ledger['files'].items():
        current = projected.get(name, (root/name).read_text())
        digest = hashlib.sha256(current.encode()).hexdigest()
        if name in projected and digest == row['before_sha256']:
            continue
        if current != row['after'] or digest != row['after_sha256']:
            raise ValueError('Unreviewed enemy healing source: '+name)
        if hashlib.sha256(row['before'].encode()).hexdigest() != row['before_sha256']:
            raise ValueError('Historical enemy healing anchor differs: '+name)
        projected[name] = row['before']
    return projected
