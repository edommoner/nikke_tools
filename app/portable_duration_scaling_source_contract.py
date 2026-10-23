"""Exact private duration-reference delta above non-core runtime."""
import hashlib,json
from pathlib import Path
def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-duration-scaling-source-delta.json').read_text())
def baseline_source(root,name,source,*,leftmost_projected=False):
    if not leftmost_projected:
        from portable_leftmost_source_contract import baseline_source as project_leftmost
        source,_=project_leftmost(root,name,source)
    row=ledger(root)['sources'].get(name)
    if row is None:return source,False
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed duration-scaling source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Ambiguous duration-scaling source: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Duration-scaling baseline changed: '+name
    return source,True
def project_sources(root,sources=None):
    from portable_leftmost_source_contract import project_sources as project_leftmost
    root=Path(root);sources,_=project_leftmost(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed duration helper: '+name
    for name in data['sources']:sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()),leftmost_projected=True)
    return sources,list(data['sources'])
