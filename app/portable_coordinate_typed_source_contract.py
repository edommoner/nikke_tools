"""Full-hash reviewed composition inverse for historical proofs, never normalization."""
from portable_removed_sources import REMOVED_SOURCES
import hashlib,json
from pathlib import Path

def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-coordinate-typed-source-delta.json').read_text())

def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_typed_geometry_source_contract import project_sources as geometry
    root=Path(root);out=geometry(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        if name in REMOVED_SOURCES:continue
        assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed typed composition dependency: '+name
    for name,row in data['sources'].items():
        if name in REMOVED_SOURCES:continue
        current=out.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed typed composition source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    return out

def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    from portable_coordinate_typed_weapon_source_contract import project_backend_source as weapons
    root=Path(root);row=ledger(root)['transport'];current=weapons(root,source)
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed coordinate typed transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']
