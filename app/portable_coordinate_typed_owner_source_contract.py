"""Exact BODY ownership delta before the retained current-damage inverse."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-coordinate-typed-owner-source-delta.json').read_text())
def checked(current,row):
    assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed typed owner source'
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_coordinate_typed_logical_owner_source_contract import project_sources as logical
    root=Path(root);out=logical(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()==digest,'Unreviewed typed owner dependency'
    for name,row in data['sources'].items():
        if name.endswith('.slang'):out[name]=checked(out.get(name,cpu_only_text(root,name,(root/name).read_text())),row)
    return out

def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    from portable_coordinate_typed_logical_owner_source_contract import project_backend_source as logical
    root=Path(root);name='app/portable_backend.py';return checked(logical(root,source),ledger(root)['sources'][name])
