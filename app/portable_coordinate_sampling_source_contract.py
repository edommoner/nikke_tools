"""Exact inverse of sampled physical hooks for historical source audits."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_coordinate_sampled_parent_source_contract import project_sources as parent_sources
    from portable_coordinate_sampled_skill_source_contract import project_sources as skill_sources
    from portable_coordinate_sampled_burst_source_contract import project_sources as burst_sources
    root=Path(root);out=parent_sources(root,skill_sources(root,burst_sources(root,sources)));d=json.loads((root/'tests/fixtures/portable-coordinate-sampling-source-delta.json').read_text())
    for name,row in d['sources'].items():
        current=out.get(name,(root/name).read_text());assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed sampled hook: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    for name,h in d['added_sources'].items():assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==h,'Unreviewed sampled implementation: '+name
    return out
def project_backend_source(root,source=None):
    root=Path(root);d=json.loads((root/'tests/fixtures/portable-coordinate-sampling-source-delta.json').read_text())['transport']
    from portable_coordinate_sampled_parent_source_contract import project_backend_source as parent_backend
    from portable_coordinate_sampled_skill_source_contract import project_backend_source as skill_backend
    from portable_coordinate_sampled_burst_source_contract import project_backend_source as burst_backend
    s=parent_backend(root,skill_backend(root,burst_backend(root,source)))
    if s!=d['current'] or hashlib.sha256(s.encode()).hexdigest()!=d['current_sha256']:raise ValueError('Unreviewed sampled transport')
    assert hashlib.sha256(d['baseline'].encode()).hexdigest()==d['baseline_sha256'];return d['baseline']
