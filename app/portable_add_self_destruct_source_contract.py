"""Exact inverse for private final-shot retirement hooks, never normalization."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    root=Path(root);ledger=json.loads((root/'tests/fixtures/portable-add-self-destruct-source-delta.json').read_text(encoding='utf-8'));out=dict(sources or {})
    if (root/'gpu/world_enemy_ammo_self_destruct_entry.slang').exists():
        from portable_enemy_ammo_combined_source_contract import project_sources as combined
        out=combined(root,out)
    if (root/'app/enemy_ammo_self_destruct_model.py').exists():
        from portable_enemy_ammo_self_destruct_source_contract import project_sources as final_queue
        out=final_queue(root,out)
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text(encoding='utf-8'))).encode()).hexdigest()!=digest:raise ValueError('Unreviewed ADD self-destruct dependency: '+name)
    for name,row in ledger['files'].items():
        current=out.get(name,cpu_only_text(root,name,(root/name).read_text(encoding='utf-8')));digest=hashlib.sha256(current.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if current!=row['after'] or digest!=row['after_sha256'] or hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:raise ValueError('Unreviewed ADD self-destruct shared source: '+name)
        out[name]=row['before']
    return out
