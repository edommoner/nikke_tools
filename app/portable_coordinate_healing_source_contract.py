"""Exact inverse for historical sampled-healing sources and transport registration."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {})
    if (root/'gpu/world_coordinate_original_entry.slang').exists():
        from portable_coordinate_original_source_contract import project_sources as original
        out=original(root,out)
    data=json.loads((root/'tests/fixtures/portable-coordinate-healing-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate-healing source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    for name,h in data['added_sources'].items():assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==h,'Unreviewed coordinate-healing addition: '+name
    return out

def project_backend_source(root,source=None):
    root=Path(root);row=json.loads((root/'tests/fixtures/portable-coordinate-healing-source-delta.json').read_text())['transport'];current=(root/row['path']).read_text() if source is None else source
    if (root/'gpu/world_coordinate_original_entry.slang').exists():
        from portable_coordinate_original_source_contract import project_backend_source as original
        current=original(root,current)
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed coordinate-healing transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']
