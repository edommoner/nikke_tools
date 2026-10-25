"""Exact source inverse; never broad normalization or a calculation proof."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_coordinate_original_enemy_stack_source_contract import project_sources as project_enemy_stacks
    from portable_coordinate_original_packet_history_source_contract import project_sources as project_history
    root=Path(root);out=project_enemy_stacks(root,project_history(root,sources));data=json.loads((root/'tests/fixtures/portable-coordinate-original-shared-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed original shared source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed original shared addition: '+name
        out.pop(name,None)
    return out
def project_backend_source(root,source=None):
    root=Path(root);row=json.loads((root/'tests/fixtures/portable-coordinate-original-shared-source-delta.json').read_text())['transport']
    current=(root/row['path']).read_text() if source is None else source
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed original shared transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']
