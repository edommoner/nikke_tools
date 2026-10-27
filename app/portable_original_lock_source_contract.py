"""Exact inverse of opt-in original-roster history banks and clock binding."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_original_health_parts_source_contract import project_sources as health_parts
    root=Path(root);out=health_parts(root,sources)
    ledger=json.loads((root/'tests/fixtures/portable-original-lock-source-delta.json').read_text())
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed original lock dependency: '+name)
    for name,row in ledger['sources'].items():
        current=out.get(name,(root/name).read_text())
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed original lock source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Historical original lock source changed: '+name)
        out[name]=row['baseline']
    return out
