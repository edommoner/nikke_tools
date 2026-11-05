"""Exact geometry/selector delta before prior typed source projections."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-typed-geometry-source-delta.json').read_text())
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_coordinate_typed_weapon_source_contract import project_sources as weapons
    root=Path(root);out=weapons(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed typed geometry dependency: '+name
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text());assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed typed geometry delta: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    return out
