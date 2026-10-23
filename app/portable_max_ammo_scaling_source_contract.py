"""Exact live-ammunition quantity delta before retained source certificates."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_heal_charge_source_contract import project_sources as project_charge
    root=Path(root);sources=project_charge(root,sources);data=json.loads((root/'tests/fixtures/portable-max-ammo-scaling-source-delta.json').read_text())
    for name,digest in data['added_sources'].items():assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text());assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed max-ammo source: '+name
        assert current==row['current'];old=row['baseline'];assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256'];sources[name]=old
    return sources
