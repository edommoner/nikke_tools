"""Reviewed opt-in source delta before legacy source projections; no normalizer."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root);data=json.loads((root/'tests/fixtures/portable-named-range-battle-source-delta.json').read_text());out=dict(sources or {})
    for name,digest in data['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise ValueError('Unreviewed named range dependency: '+name)
    for name,row in data['files'].items():
        source=out.get(name,(root/name).read_text());digest=hashlib.sha256(source.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if source!=row['after'] or digest!=row['after_sha256'] or hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:raise ValueError('Unreviewed named range shared source: '+name)
        out[name]=row['before']
    return out
