"""Full-hash reviewed composition inverse for historical proofs, never normalization."""
import hashlib,json
from pathlib import Path

def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-coordinate-typed-source-delta.json').read_text())

def project_sources(root,sources=None):
    from portable_typed_geometry_source_contract import project_sources as geometry
    root=Path(root);out=geometry(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed typed composition dependency: '+name
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed typed composition source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    return out

def project_backend_source(root,source=None):
    root=Path(root);row=ledger(root)['transport'];current=(root/'app/portable_backend.py').read_text() if source is None else source
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed coordinate typed transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']
