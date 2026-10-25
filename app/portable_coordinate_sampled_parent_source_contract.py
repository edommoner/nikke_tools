"""Exact inverse of parent-ratio admission and capture; no cache rebinding."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});d=json.loads((root/'tests/fixtures/portable-coordinate-sampled-parent-source-delta.json').read_text())
    for name,row in d['sources'].items():
        current=out.get(name,(root/name).read_text());assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed sampled parent source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    for name,h in d['added_sources'].items():assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==h,'Unreviewed sampled parent addition: '+name
    return out
def project_backend_source(root,source=None):
    root=Path(root);d=json.loads((root/'tests/fixtures/portable-coordinate-sampled-parent-source-delta.json').read_text())['transport'];s=(root/d['path']).read_text() if source is None else source
    if s!=d['current'] or hashlib.sha256(s.encode()).hexdigest()!=d['current_sha256']:raise ValueError('Unreviewed sampled parent transport')
    assert hashlib.sha256(d['baseline'].encode()).hexdigest()==d['baseline_sha256'];return d['baseline']
