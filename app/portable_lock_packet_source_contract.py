"""Exact inverse of opt-in receipt links; at+7 remains periodic-owned."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_live_lock_source_contract import project_sources as live
    root=Path(root);out=live(root,sources)
    ledger=json.loads((root/'tests/fixtures/portable-lock-packet-source-delta.json').read_text())
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed lock packet dependency: '+name)
    for name,row in ledger['sources'].items():
        current=out.get(name,cpu_only_text(root,name,(root/name).read_text()))
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed lock packet source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Historical lock packet source changed: '+name)
        out[name]=row['baseline']
    return out
