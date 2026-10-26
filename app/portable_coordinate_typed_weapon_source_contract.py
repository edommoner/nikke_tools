"""Exact inverse of the physical hook delta, before prior source projections."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-coordinate-typed-weapon-source-delta.json').read_text(encoding='utf-8'))
def checked(current,row):
    assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed typed physical source'
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
    return row['baseline']
def project_sources(root,sources=None):
    from portable_coordinate_typed_aim_source_contract import project_sources as aims
    root=Path(root);out=aims(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Unreviewed typed physical dependency: '+name
    for name,row in data['sources'].items():
        if name.endswith('.slang'):out[name]=checked(out.get(name,(root/name).read_text()),row)
    return out

def project_backend_source(root,source=None):
    root=Path(root);name='app/portable_backend.py'
    from portable_coordinate_typed_aim_source_contract import project_backend_source as aims
    try:return checked(aims(root,source),ledger(root)['sources'][name])
    except AssertionError as error:raise ValueError('Unreviewed typed physical transport') from error
