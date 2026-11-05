"""Exact inverse for the opt-in manual/lock composition, never normalization."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_lock_packet_source_contract import project_sources as packets
    root=Path(root);out=packets(root,sources)
    ledger=json.loads((root/'tests/fixtures/portable-physical-lock-cover-source-delta.json').read_text())
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed physical cover dependency: '+name)
    for name,row in ledger['sources'].items():
        current=out.get(name,cpu_only_text(root,name,(root/name).read_text()))
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed physical cover source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Historical physical cover source changed: '+name)
        out[name]=row['baseline']
    return out

def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    name='app/portable_backend.py'
    try:return project_sources(root,{} if source is None else {name:source})[name]
    except AssertionError as error:raise ValueError(str(error)) from error
