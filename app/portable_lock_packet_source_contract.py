"""Exact inverse of opt-in receipt links; at+7 remains periodic-owned."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_live_lock_source_contract import project_sources as live
    root=Path(root);out=live(root,sources)
    ledger=json.loads((root/'tests/fixtures/portable-lock-packet-source-delta.json').read_text())
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed lock packet dependency: '+name)
    for name,row in ledger['sources'].items():
        current=out.get(name,(root/name).read_text())
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed lock packet source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Historical lock packet source changed: '+name)
        out[name]=row['baseline']
    return out
