"""Exact inverse of composed layout changes for retained historical audits."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {})
    data=json.loads((root/'tests/fixtures/portable-arena-composed-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed arena composition source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
        sources[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed composed entry: '+name
    return sources
