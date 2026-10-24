"""Exact authored-aim inverse for historical audits; strict normalization unchanged."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_coordinate_control_source_contract import project_sources as project_control
    root=Path(root);sources=project_control(root,sources);data=json.loads((root/'tests/fixtures/portable-coordinate-aim-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed authored aim source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
        sources[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert hashlib.sha256(current.encode()).hexdigest()==digest,'Unreviewed authored aim addition: '+name
    return sources

def project_backend_source(root,source=None):
    root=Path(root);row=json.loads((root/'tests/fixtures/portable-coordinate-aim-source-delta.json').read_text())['transport']
    from portable_coordinate_control_source_contract import project_backend_source as project_control
    current=project_control(root,source)
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed authored aim transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
    return row['baseline']
