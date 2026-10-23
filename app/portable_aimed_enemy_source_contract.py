"""Exact aimed logical enemy continuation delta; existing arithmetic stays anchored."""
import hashlib, json
from pathlib import Path


def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-aimed-enemy-source-delta.json').read_text())


def baseline_source(root, name, source):
    from portable_squad_stage_source_contract import baseline_source as project_stage
    source, _ = project_stage(root, name, source)
    rows = ledger(root)['sources']
    if name not in rows:
        return source, False
    row = rows[name]
    assert hashlib.sha256(source.encode()).hexdigest() == row['current_sha256'], 'Unreviewed aimed logical enemy source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current']) == 1, 'Ambiguous aimed logical enemy delta: '+name
        source = source.replace(change['current'], change['baseline'], 1)
    assert hashlib.sha256(source.encode()).hexdigest() == row['baseline_sha256'], 'Aimed logical enemy historical source changed: '+name
    return source, True


def project_sources(root, sources=None):
    from portable_squad_stage_source_contract import project_sources as project_stage
    root = Path(root); sources, _ = project_stage(root, sources)
    for name in ledger(root)['sources']:
        sources[name], _ = baseline_source(root, name, sources.get(name, (root/name).read_text()))
    return sources, list(ledger(root)['sources'])
