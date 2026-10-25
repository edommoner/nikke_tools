"""Exact mixed-node inverse for retained historical source/transport audits."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_coordinate_sampling_source_contract import project_sources as project_sampling
    root=Path(root);sources=project_sampling(root,sources);data=json.loads((root/'tests/fixtures/portable-coordinate-mixed-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed mixed coordinate source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];sources[name]=row['baseline']
    for name,h in data['added_sources'].items():assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==h,'Unreviewed mixed coordinate addition: '+name
    return sources

def project_backend_source(root,source=None):
    root=Path(root);row=json.loads((root/'tests/fixtures/portable-coordinate-mixed-source-delta.json').read_text())['transport']
    from portable_coordinate_sampling_source_contract import project_backend_source as project_sampling
    current=project_sampling(root,source)
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed mixed coordinate transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']
