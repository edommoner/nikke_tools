"""Exact inverse for private final-shot retirement hooks, never normalization."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    root=Path(root);ledger=json.loads((root/'tests/fixtures/portable-add-self-destruct-source-delta.json').read_text(encoding='utf-8'));out=dict(sources or {})
    if (root/'app/enemy_ammo_self_destruct_model.py').exists():
        from portable_enemy_ammo_self_destruct_source_contract import project_sources as final_queue
        out=final_queue(root,out)
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text(encoding='utf-8')).encode()).hexdigest()!=digest:raise ValueError('Unreviewed ADD self-destruct dependency: '+name)
    for name,row in ledger['files'].items():
        current=out.get(name,(root/name).read_text(encoding='utf-8'));digest=hashlib.sha256(current.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if current!=row['after'] or digest!=row['after_sha256'] or hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:raise ValueError('Unreviewed ADD self-destruct shared source: '+name)
        out[name]=row['before']
    return out
