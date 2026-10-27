"""Exact inverse of opt-in receipt links; at+7 remains periodic-owned."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_lock_enemy_carrier_source_contract import project_sources as enemy
    root=Path(root);out=enemy(root,sources)
    ledger=json.loads((root/'tests/fixtures/portable-packet-fates-source-delta.json').read_text())
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed packet fates dependency: '+name)
    for name,row in ledger['sources'].items():
        current=out.get(name,(root/name).read_text())
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed packet fates source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Historical packet fates source changed: '+name)
        out[name]=row['baseline']
    return out
