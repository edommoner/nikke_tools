"""Exact inverse of the physical hook delta, before prior source projections."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-coordinate-typed-weapon-source-delta.json').read_text(encoding='utf-8'))
def checked(current,row):
    assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed typed physical source'
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
    return row['baseline']
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_coordinate_typed_aim_source_contract import project_sources as aims
    root=Path(root);out=aims(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        current=out[name].encode() if name in out else cpu_only_bytes(root,name,(root/name).read_bytes())
        assert hashlib.sha256(current).hexdigest()==digest,'Unreviewed typed physical dependency: '+name
    for name,row in data['sources'].items():
        if name.endswith('.slang'):out[name]=checked(out.get(name,cpu_only_text(root,name,(root/name).read_text())),row)
    return out

def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    root=Path(root);name='app/portable_backend.py'
    from portable_coordinate_typed_aim_source_contract import project_backend_source as aims
    try:return checked(aims(root,source),ledger(root)['sources'][name])
    except AssertionError as error:raise ValueError('Unreviewed typed physical transport') from error
