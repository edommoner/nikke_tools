"""Exact inverse of the reviewed wide DoT membership fix, no broad normalization."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});data=json.loads((root/'tests/fixtures/portable-coordinate-original-enemy-stack-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed enemy-stack source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    return out
