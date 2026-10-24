"""Exact control-composition inverse for historical source audits only."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {});data=json.loads((root/'tests/fixtures/portable-coordinate-control-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed control composition source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
        sources[name]=row['baseline']
    for name,digest in data['added_sources'].items():assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed control composition addition: '+name
    return sources

def project_backend_source(root,source=None):
    root=Path(root);row=json.loads((root/'tests/fixtures/portable-coordinate-control-source-delta.json').read_text())['transport'];current=(root/row['path']).read_text() if source is None else source
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed control composition transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
    return row['baseline']
