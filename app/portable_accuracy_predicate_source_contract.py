"""Finite accuracy stat predicate admission delta."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-accuracy-predicate-source-delta.json').read_text())
def baseline_source(root,name,source):
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed accuracy-predicate source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Missing or ambiguous accuracy-predicate delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Manual-swap historical source changed: '+name
    return source,True
def project_sources(root,sources=None,*,undying_projected=False):
    root=Path(root);sources=dict(sources or {});data=ledger(root)
    if not undying_projected:
        from portable_undying_predicate_source_contract import project_sources as project_undying
        sources,_=project_undying(root,sources)
    for name in data['sources']:sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()))
    return sources,list(data['sources'])
