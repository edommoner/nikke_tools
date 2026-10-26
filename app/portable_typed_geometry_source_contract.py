"""Exact geometry/selector delta before prior typed source projections."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-typed-geometry-source-delta.json').read_text())
def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});data=ledger(root)
    for name,digest in data['added_sources'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Unreviewed typed geometry dependency: '+name
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text());assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed typed geometry delta: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    return out
