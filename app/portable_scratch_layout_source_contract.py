"""Reversible relocation of private state; numerical statements stay anchored."""
import hashlib, json
from pathlib import Path


def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-scratch-layout-source-delta.json').read_text())


def baseline_source(root, name, source, *, interrupt_projected=False):
    from portable_interrupt_aim_source_contract import baseline_source as project_interrupt
    if not interrupt_projected:source, _ = project_interrupt(root, name, source)
    rows = ledger(root)['sources']
    if name not in rows:
        return source, False
    row = rows[name]
    assert hashlib.sha256(source.encode()).hexdigest() == row['current_sha256'], 'Unreviewed scratch layout source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current']) == 1, 'Ambiguous scratch layout delta: '+name
        source = source.replace(change['current'], change['baseline'], 1)
    assert hashlib.sha256(source.encode()).hexdigest() == row['baseline_sha256'], 'Scratch layout baseline changed: '+name
    return source, True


def project_sources(root, sources=None):
    from portable_interrupt_aim_source_contract import project_sources as project_interrupt
    root = Path(root); sources, _ = project_interrupt(root, sources)
    for name in ledger(root)['sources']:
        sources[name], _ = baseline_source(root, name, sources.get(name, (root/name).read_text()), interrupt_projected=True)
    return sources, list(ledger(root)['sources'])
