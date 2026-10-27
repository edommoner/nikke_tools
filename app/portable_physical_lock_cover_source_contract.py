"""Exact inverse for the opt-in manual/lock composition, never normalization."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_lock_packet_source_contract import project_sources as packets
    root=Path(root);out=packets(root,sources)
    ledger=json.loads((root/'tests/fixtures/portable-physical-lock-cover-source-delta.json').read_text())
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed physical cover dependency: '+name)
    for name,row in ledger['sources'].items():
        current=out.get(name,(root/name).read_text())
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed physical cover source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Historical physical cover source changed: '+name)
        out[name]=row['baseline']
    return out

def project_backend_source(root,source=None):
    name='app/portable_backend.py'
    try:return project_sources(root,{} if source is None else {name:source})[name]
    except AssertionError as error:raise ValueError(str(error)) from error
