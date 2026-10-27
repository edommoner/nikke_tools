"""Exact reviewed opt-in query inverse, never a generated-code normalizer."""
import hashlib,json
from pathlib import Path

def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-effect-target-count-source-delta.json').read_text())

def project_sources(root,sources=None):
    from portable_effect_target_count_shot_source_contract import project_sources as shots
    root=Path(root);out=shots(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        current=out.get(name,(root/name).read_text())
        if hashlib.sha256(current.encode()).hexdigest()!=digest:raise AssertionError('Unreviewed target-count dependency: '+name)
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:
            raise AssertionError('Unreviewed target-count source: '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:
            raise AssertionError('Target-count historical baseline changed: '+name)
        out[name]=row['baseline']
    return out
