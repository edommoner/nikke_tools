"""Exact reversible history extension, layered before the numeric-query delta."""
import hashlib,json
from pathlib import Path


def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-ordered-history-source-delta.json').read_text())


def baseline_source(root,name,source,*,diagnostic_projected=False):
    if not diagnostic_projected:
        from portable_query_diagnostic_source_contract import baseline_source as project_diagnostic
        source,_=project_diagnostic(root,name,source)
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed ordered history source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Ambiguous ordered history delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Ordered history baseline changed: '+name
    return source,True


def project_sources(root,sources=None):
    from portable_query_diagnostic_source_contract import project_sources as project_diagnostic
    root=Path(root);sources,_=project_diagnostic(root,sources);rows=ledger(root)['sources']
    for name in rows:sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()),diagnostic_projected=True)
    return sources,list(rows)
