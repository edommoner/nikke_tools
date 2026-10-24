"""Exact cache-to-core inverse for historical source audits only."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {})
    data=json.loads((root/'tests/fixtures/portable-coordinate-cache-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate cache source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
        sources[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed added coordinate cache source: '+name
    return sources


def project_backend_source(root,source=None):
    root=Path(root);row=json.loads((root/'tests/fixtures/portable-coordinate-cache-source-delta.json').read_text())['transport']
    current=(root/row['path']).read_text() if source is None else source
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed coordinate cache transport source')
    if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise ValueError('Coordinate core transport baseline changed')
    return row['baseline']
