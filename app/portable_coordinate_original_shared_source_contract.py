"""Exact source inverse; never broad normalization or a calculation proof."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_coordinate_original_enemy_stack_source_contract import project_sources as project_enemy_stacks
    from portable_coordinate_original_packet_history_source_contract import project_sources as project_history
    from portable_coordinate_typed_source_contract import project_sources as typed
    root=Path(root);out=project_enemy_stacks(root,project_history(root,typed(root,sources)));data=json.loads((root/'tests/fixtures/portable-coordinate-original-shared-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed original shared source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed original shared addition: '+name
        out.pop(name,None)
    return out
def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    from portable_coordinate_typed_source_contract import project_backend_source as typed
    root=Path(root);source=typed(root,source);row=json.loads((root/'tests/fixtures/portable-coordinate-original-shared-source-delta.json').read_text())['transport']
    current=(root/row['path']).read_text() if source is None else source
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed original shared transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']
