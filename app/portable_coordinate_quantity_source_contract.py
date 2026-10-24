"""Exact current-to-physical-v1 inverse for historical source audits only."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    from portable_coordinate_accum_emission_source_contract import project_sources as project_emission
    root=Path(root);sources=project_emission(root,sources)
    data=json.loads((root/'tests/fixtures/portable-coordinate-quantity-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate quantity source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
        sources[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed added coordinate quantity source: '+name
    return sources
