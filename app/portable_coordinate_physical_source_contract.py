"""Exact reviewed inverse for historical audits, never a GPU normalizer."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    from portable_coordinate_quantity_source_contract import project_sources as project_quantity
    root=Path(root);sources=project_quantity(root,sources)
    data=json.loads((root/'tests/fixtures/portable-coordinate-physical-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate physical source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
        sources[name]=row['baseline']
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed coordinate physical added source: '+name
    return sources


def project_backend_source(root,source=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if source is not None:source=cpu_boundary_text(root,'app/portable_backend.py',source)
    root=Path(root)
    row=json.loads((root/'tests/fixtures/portable-coordinate-physical-source-delta.json').read_text())['transport']
    from portable_coordinate_core_source_contract import project_backend_source as project_core_backend
    current=project_core_backend(root,source)
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:
        raise ValueError('Unreviewed coordinate physical transport source')
    if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:
        raise ValueError('Coordinate physical transport baseline changed')
    return row['baseline']
