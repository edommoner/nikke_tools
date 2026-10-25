"""Exact source inverse; never broad normalization or a calculation proof."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {})
    if (root/'gpu/world_coordinate_original_slot_entry.slang').exists():
        from portable_coordinate_original_slot_source_contract import project_sources as slots
        out=slots(root,out)
    data=json.loads((root/'tests/fixtures/portable-coordinate-original-cleanse-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed original cleanse source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed original cleanse addition: '+name
        out.pop(name,None)
    return out
def project_backend_source(root,source=None):
    root=Path(root);row=json.loads((root/'tests/fixtures/portable-coordinate-original-cleanse-source-delta.json').read_text())['transport']
    current=(root/row['path']).read_text() if source is None else source
    if (root/'gpu/world_coordinate_original_slot_entry.slang').exists():
        from portable_coordinate_original_slot_source_contract import project_backend_source as slots
        current=slots(root,current)
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed original cleanse transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']
