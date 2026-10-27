"""Exact physical observation delta before the original capacity source audit."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-effect-target-count-shot-source-delta.json').read_text())

def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});data=ledger(root)
    for name,digest in data['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:
            raise AssertionError('Unreviewed physical target-count dependency: '+name)
    for name,row in data['sources'].items():
        current=out.get(name,(root/name).read_text())
        if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:
            label='dependency' if name=='gpu/effect_target_count_runtime.slang' else 'source'
            raise AssertionError('Unreviewed target-count '+label+': '+name)
        if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:
            raise AssertionError('Physical target-count historical baseline changed: '+name)
        out[name]=row['baseline']
    return out
