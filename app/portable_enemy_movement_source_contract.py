"""Exact small-hunk inverse of opt-in movement hooks; not a normalizer."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});data=json.loads((root/'tests/fixtures/portable-enemy-movement-source-delta.json').read_text())
    if (root/'gpu/world_moving_typed_entry.slang').exists():
        from portable_moving_typed_source_contract import project_sources as moving_typed
        out=moving_typed(root,out)
    for name,digest in data['added_sources'].items():
        value=out.get(name,(root/name).read_text())
        if hashlib.sha256(value.encode()).hexdigest()!=digest:raise ValueError('Unreviewed movement dependency: '+name)
    for name,row in data['files'].items():
        value=out.get(name,(root/name).read_text());digest=hashlib.sha256(value.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if digest!=row['after_sha256']:raise ValueError('Unreviewed movement shared source: '+name)
        for hunk in reversed(row['hunks']):
            if value.count(hunk['after'])!=1:raise ValueError('Movement inverse hunk is ambiguous')
            value=value.replace(hunk['after'],hunk['before'],1)
        if hashlib.sha256(value.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Movement source inverse differs')
        out[name]=value
    return out
