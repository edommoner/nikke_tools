"""Exact notification-local parent fixed damage delta before all prior proofs."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_max_ammo_scaling_source_contract import project_sources as project_ammo
    root=Path(root);sources=project_ammo(root,sources);data=json.loads((root/'tests/fixtures/portable-parent-fixed-source-delta.json').read_text())
    for name,digest in data['added_sources'].items():assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text());assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed parent fixed source: '+name
        assert current==row['current'];old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources
