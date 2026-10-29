"""Restore the reviewed append audit only for the original extraction proof."""
import hashlib,json
from pathlib import Path


def project_generation_source(root,source=None):
    root=Path(root);name='app/portable_slang_generation.py'
    row=json.loads((root/'tests/fixtures/portable-generation-append-audit-delta.json').read_text())
    source=(root/name).read_text() if source is None else source
    digest=lambda text:hashlib.sha256(text.encode()).hexdigest()
    if digest(source)!=row['current_sha256']:raise ValueError('Unreviewed generation extraction source')
    for h in reversed(row['hunks']):
        if source.count(h['after'])!=1:raise ValueError('Ambiguous generation extraction inverse')
        source=source.replace(h['after'],h['before'],1)
    if digest(source)!=row['baseline_sha256']:raise ValueError('Generation extraction baseline changed')
    return source
