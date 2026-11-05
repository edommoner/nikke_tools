"""Exact opt-in inverse, retaining approved downstream movement preimages."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
from portable_removed_sources import REMOVED_SOURCES
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_moving_many_source_contract import project_sources as maximum_slots
    sources=maximum_slots(root,sources)
    root=Path(root);out=dict(sources or {});ledger=json.loads((root/'tests/fixtures/portable-moving-typed-source-delta.json').read_text())
    downstream=json.loads((root/'tests/fixtures/portable-enemy-movement-source-delta.json').read_text())['files']
    for name,digest in ledger['added_sources'].items():
        if name in REMOVED_SOURCES:continue
        if hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()!=digest:raise ValueError('Unreviewed moving typed dependency: '+name)
    for name,row in ledger['files'].items():
        if name in REMOVED_SOURCES:continue
        value=out.get(name,cpu_only_text(root,name,(root/name).read_text()));digest=hashlib.sha256(value.encode()).hexdigest()
        if name in out and digest in {row['before_sha256'],downstream.get(name,{}).get('before_sha256')}:continue
        if digest!=row['after_sha256']:raise ValueError('Unreviewed moving typed shared source: '+name)
        for h in reversed(row['hunks']):
            if value.count(h['after'])!=1:raise ValueError('Ambiguous moving typed inverse')
            value=value.replace(h['after'],h['before'],1)
        if hashlib.sha256(value.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Moving typed inverse differs')
        out[name]=value
    return out
