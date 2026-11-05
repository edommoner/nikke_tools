"""Reviewed opt-in source delta before legacy source projections; no normalizer."""
from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes, reviewed_text as cpu_only_text
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_cpu_only_source_contract import reviewed_text as cpu_boundary_text
    if sources is not None:sources={name:cpu_boundary_text(root,name,text) for name,text in sources.items()}
    root=Path(root);data=json.loads((root/'tests/fixtures/portable-named-range-battle-source-delta.json').read_text());out=dict(sources or {})
    if sources is None and (root/'gpu/world_add_attack_battle_entry.slang').exists():
        # Direct audits need the same newer-to-older exact inverse chain as
        # the existing enemy-healing parent. Do not normalize current bytes.
        from portable_add_attack_battle_source_contract import project_sources as add_attacks
        out=add_attacks(root)
    for name,digest in data['added_sources'].items():
        if hashlib.sha256(out.get(name,cpu_only_text(root,name,(root/name).read_text())).encode()).hexdigest()!=digest:raise ValueError('Unreviewed named range dependency: '+name)
    for name,row in data['files'].items():
        source=out.get(name,cpu_only_text(root,name,(root/name).read_text()));digest=hashlib.sha256(source.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if source!=row['after'] or digest!=row['after_sha256'] or hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:raise ValueError('Unreviewed named range shared source: '+name)
        out[name]=row['before']
    return out
