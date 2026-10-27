"""Exact reviewed resident arc storage inverse, never a GPU normalizer."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-coordinate-resident-arc-source-delta.json').read_text())
def checked(current,row,*,error_type=AssertionError):
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise error_type('Unreviewed resident arc source')
    if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise error_type('Resident arc baseline changed')
    return row['baseline']
def project_sources(root,sources=None):
    from portable_dispatch_frame_source_contract import project_sources as frames
    root=Path(root);out=frames(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed resident arc dependency: '+name)
    for name,row in data['sources'].items():
        if name!='app/portable_backend.py':out[name]=checked(out.get(name,(root/name).read_text()),row)
    return out
def project_backend_source(root,source=None):
    root=Path(root);name='app/portable_backend.py';return checked((root/name).read_text() if source is None else source,ledger(root)['sources'][name],error_type=ValueError)
