"""Exact reviewed GPU frame-storage inverse, never a generated-code normalizer."""
import hashlib,json
from pathlib import Path

def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-dispatch-frame-source-delta.json').read_text())

def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});data=ledger(root)
    for name,digest in data['added_sources'].items():
        actual=out.get(name,(root/name).read_text())
        if hashlib.sha256(actual.encode()).hexdigest()!=digest:raise AssertionError('Unreviewed dispatch frame dependency: '+name)
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed dispatch frame source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Dispatch frame historical baseline changed: '+name)
        out[name]=row['baseline']
    return out
