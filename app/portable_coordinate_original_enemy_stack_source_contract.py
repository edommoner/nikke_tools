"""Exact inverse of the reviewed wide DoT membership fix, no broad normalization."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});data=json.loads((root/'tests/fixtures/portable-coordinate-original-enemy-stack-source-delta.json').read_text())
    from portable_weighted_incoming_source_contract import reference_engine_preimages
    preimages=reference_engine_preimages(root)
    for name,row in data['sources'].items():
        actual=(root/name).read_text();current=out.get(name,actual)
        # Only the exact reviewed current file can borrow its old bytes. An
        # explicit source mutation must still fail the original strict inverse.
        if current==actual:current=preimages.get(name,current)
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed enemy-stack source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];out[name]=row['baseline']
    return out
