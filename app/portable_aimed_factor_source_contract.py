"""Exact aimed factor consumer delta; existing binary64 arithmetic stays anchored."""
import hashlib, json
from pathlib import Path


def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-aimed-factor-source-delta.json').read_text())


def baseline_source(root, name, source, *, area_projected=False):
    from portable_aimed_area_source_contract import baseline_source as project_area
    if not area_projected:source, _ = project_area(root, name, source)
    rows = ledger(root)['sources']
    if name not in rows:
        return source, False
    row = rows[name]
    assert hashlib.sha256(source.encode()).hexdigest() == row['current_sha256'], 'Unreviewed aimed factor source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current']) == 1, 'Ambiguous aimed factor delta: '+name
        source = source.replace(change['current'], change['baseline'], 1)
    assert hashlib.sha256(source.encode()).hexdigest() == row['baseline_sha256'], 'Aimed factor historical source changed: '+name
    return source, True


def project_sources(root, sources=None):
    from portable_aimed_area_source_contract import project_sources as project_area
    root = Path(root); sources, _ = project_area(root, sources)
    for name in ledger(root)['sources']:
        sources[name], _ = baseline_source(root, name, sources.get(name, (root/name).read_text()), area_projected=True)
    return sources, list(ledger(root)['sources'])
