"""Exact inverse of sampled burst RNG hooks for historical source certificates."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
from portable_removed_sources import REMOVED_SOURCES
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    root=Path(root);out=dict(sources or {});d=json.loads((root/'tests/fixtures/portable-coordinate-sampled-burst-source-delta.json').read_text())
    for name,row in d['sources'].items():
        if name in REMOVED_SOURCES:continue
        current=out.get(name,cpu_only_text(root,name,(root/name).read_text()));assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed sampled burst source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    for name,h in d['added_sources'].items():
        if name in REMOVED_SOURCES:continue
        assert hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()==h,'Unreviewed sampled burst addition: '+name
    return out
def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    root=Path(root);d=json.loads((root/'tests/fixtures/portable-coordinate-sampled-burst-source-delta.json').read_text())['transport'];s=(root/d['path']).read_text() if source is None else source
    if s!=d['current'] or hashlib.sha256(s.encode()).hexdigest()!=d['current_sha256']:raise ValueError('Unreviewed sampled burst transport')
    assert hashlib.sha256(d['baseline'].encode()).hexdigest()==d['baseline_sha256'];return d['baseline']
