"""Exact reviewed transport inverse, used only by historical source audits."""
import hashlib,json
from pathlib import Path


def historical_backend_source(root,source=None):
    from portable_coordinate_physical_source_contract import project_backend_source
    root=Path(root)
    row=json.loads((root/'tests/fixtures/portable-arena-transport-source-delta.json').read_text())
    current=project_backend_source(root,source)
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:
        raise ValueError('Unreviewed composed transport source')
    baseline=row['baseline']
    if hashlib.sha256(baseline.encode()).hexdigest()!=row['baseline_sha256']:
        raise ValueError('Historical transport baseline changed')
    return baseline
