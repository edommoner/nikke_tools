"""Exact inverse of complete packet history, preserving prior source contracts."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    root=Path(root);out=dict(sources or {});data=json.loads((root/'tests/fixtures/portable-coordinate-original-packet-history-source-delta.json').read_text())
    # A direct caller needs the same exact newer typed inverse that the
    # shared-source chain already supplies before this older ledger.
    if not any(name in out for name in data['sources']) and (root/'gpu/world_coordinate_typed_entry.slang').exists():
        from portable_coordinate_typed_source_contract import project_sources as typed
        out=typed(root,out)
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed packet history source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed packet history addition: '+name
        out.pop(name,None)
    return out
