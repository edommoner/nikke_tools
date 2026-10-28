"""Exact inverse for one explicitly registered original health/parts entry."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {})
    if (root/'gpu/world_enemy_healing_entry.slang').exists():
        from portable_enemy_healing_source_contract import project_sources as healing
        out=healing(root,out)
    if (root/'gpu/world_coordinate_logical_actor_entry.slang').exists():
        from portable_logical_geometry_source_contract import project_sources as logical
        out=logical(root,out)
    if (root/'gpu/world_coordinate_typed_history_entry.slang').exists():
        from portable_skill_history_source_contract import project_sources as history
        out=history(root,out)
    ledger=json.loads((root/'tests/fixtures/portable-original-health-parts-source-delta.json').read_text())
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed original health/parts dependency: '+name)
    for name,row in ledger['sources'].items():
        current=out.get(name,(root/name).read_text())
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed original health/parts source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Historical original health/parts source changed: '+name)
        out[name]=row['baseline']
    return out
