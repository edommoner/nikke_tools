"""Exact private partial-charge continuation delta; arithmetic remains anchored."""
import hashlib,json
from pathlib import Path


def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-partial-charge-source-delta.json').read_text())

def baseline_source(root,name,source,*,notcore_projected=False):
    if not notcore_projected:
        from portable_not_core_source_contract import baseline_source as project_notcore
        source,_=project_notcore(root,name,source)
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed partial-charge source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Ambiguous partial-charge source: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Partial-charge baseline changed: '+name
    return source,True

def project_sources(root,sources=None):
    from portable_not_core_source_contract import project_sources as project_notcore
    root=Path(root);sources,_=project_notcore(root,sources)
    for name in ledger(root)['sources']:sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()),notcore_projected=True)
    return sources,list(ledger(root)['sources'])
