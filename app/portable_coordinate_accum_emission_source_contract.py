"""Exact emission-to-quantity inverse for historical source audits only."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    from portable_coordinate_core_source_contract import project_sources as project_core
    root=Path(root);sources=project_core(root,sources)
    data=json.loads((root/'tests/fixtures/portable-coordinate-accum-emission-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate accumulation emission source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
        sources[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed added coordinate accumulation emission source: '+name
    return sources
