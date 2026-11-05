"""Full-hash inverse for the explicit typed frame aim hooks; no normalization."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-coordinate-typed-aim-source-delta.json').read_text())
def checked(current,row):
    assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed typed aim source'
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
    return row['baseline']
def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_coordinate_typed_actor_source_contract import project_sources as actors
    root=Path(root);out=actors(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()==digest,'Unreviewed typed aim dependency'
    for name,row in data['sources'].items():
        if name.endswith('.slang'):
            current=out.get(name,cpu_only_text(root,name,(root/name).read_text()))
            if name=='gpu/coordinate_aim_runtime.slang' and name not in out:
                from portable_weighted_incoming_source_contract import reference_engine_preimages
                current=reference_engine_preimages(root)[name]
            out[name]=checked(current,row)
    return out

def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    from portable_coordinate_typed_actor_source_contract import project_backend_source as actors
    root=Path(root);name='app/portable_backend.py';return checked(actors(root,source),ledger(root)['sources'][name])
