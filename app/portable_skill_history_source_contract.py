"""Exact inverse of history address/capacity hooks and registered transport."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-skill-history-source-delta.json').read_text())
def checked(current,row):
    assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed shared skill history source'
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'],'Shared skill history baseline changed'
    return row['baseline']
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    root=Path(root);out=dict(sources or {});data=ledger(root)
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()==digest,'Unreviewed shared skill history dependency'
    for name,row in data['sources'].items():
        out[name]=checked(out.get(name,cpu_only_text(root,name,(root/name).read_text())),row)
    return out
def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    root=Path(root);name='app/portable_backend.py'
    if (root/'gpu/world_coordinate_logical_actor_entry.slang').exists():
        from portable_logical_geometry_source_contract import project_backend_source as logical_backend
        source=logical_backend(root,source)
    try:return checked(cpu_only_text(root,name,(root/name).read_text()) if source is None else source,ledger(root)['sources'][name])
    except AssertionError as error:raise ValueError('Unreviewed shared skill history transport') from error
