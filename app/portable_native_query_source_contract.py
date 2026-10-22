"""Exact reversible delta for the shared native numeric-query connection."""
import hashlib
import json
from pathlib import Path


def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-native-query-source-delta.json').read_text())


def baseline_source(root,name,source,*,history_projected=False):
    if not history_projected:
        from portable_ordered_history_source_contract import baseline_source as project_history
        source,_=project_history(root,name,source)
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed native query source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Ambiguous native query delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Native query historical source changed: '+name
    return source,True


def project_sources(root, sources=None):
    from portable_ordered_history_source_contract import project_sources as project_history
    root=Path(root);sources,_=project_history(root,sources);data=ledger(root)
    for name in data['sources']:
        sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()),history_projected=True)
    return sources,list(data['sources'])
