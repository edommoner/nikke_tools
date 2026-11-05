"""Exact inverse of opt-in original-roster history banks and clock binding."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_original_health_parts_source_contract import project_sources as health_parts
    root=Path(root)
    try:out=health_parts(root,sources)
    except ValueError as error:
        # Preserve this historical auditor's public rejection type when a
        # newer nested source guard rejects the same unreviewed mutation.
        if not str(error).startswith('Unreviewed'):raise
        raise AssertionError(str(error)) from error
    ledger=json.loads((root/'tests/fixtures/portable-original-lock-source-delta.json').read_text())
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed original lock dependency: '+name)
    for name,row in ledger['sources'].items():
        current=out.get(name,cpu_only_text(root,name,(root/name).read_text()))
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed original lock source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Historical original lock source changed: '+name)
        out[name]=row['baseline']
    return out
