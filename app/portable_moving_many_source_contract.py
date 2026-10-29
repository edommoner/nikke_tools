"""Exact inverse of the wide observation banks; no generated-code exclusions."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {})
    ledger=json.loads((root/'tests/fixtures/portable-moving-many-source-delta.json').read_text())
    older=[json.loads((root/'tests/fixtures'/name).read_text())['files'] for name in ('portable-moving-typed-source-delta.json','portable-enemy-movement-source-delta.json')]
    digest=lambda value:hashlib.sha256(value.encode()).hexdigest()
    for name,expected in ledger['added_sources'].items():
        if digest(out.get(name,(root/name).read_text()))!=expected:raise ValueError('Unreviewed maximum-slot dependency: '+name)
    for name,row in ledger['files'].items():
        value=out.get(name,(root/name).read_text());sha=digest(value)
        allowed={row['before_sha256'],*[old.get(name,{}).get('before_sha256') for old in older]}
        if name in out and sha in allowed:continue
        if sha!=row['after_sha256']:raise ValueError('Unreviewed maximum-slot source: '+name)
        for h in reversed(row['hunks']):
            if value.count(h['after'])!=1:raise ValueError('Ambiguous maximum-slot inverse')
            value=value.replace(h['after'],h['before'],1)
        if digest(value)!=row['before_sha256']:raise ValueError('Maximum-slot inverse differs')
        out[name]=value
    return out
