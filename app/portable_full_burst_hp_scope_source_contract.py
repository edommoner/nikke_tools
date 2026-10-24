"""Exact HP-scope correction over the retained failed query package."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_parent_fixed_source_contract import project_sources as project_parent
    from portable_coordinate_full_burst_source_contract import project_sources as project_coordinates
    root=Path(root);sources=project_coordinates(root,project_parent(root,sources));data=json.loads((root/'tests/fixtures/portable-full-burst-hp-scope-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text());assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed full-burst HP scope: '+name
        assert current==row['current'];old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources
