"""Exact private final-defense selector delta before the prior source proofs."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-below-def-source-delta.json').read_text())
def baseline_source(root,name,source,*,burst1_projected=False):
    if not burst1_projected:
        from portable_burst1_ally_source_contract import baseline_source as project_burst1
        source,_=project_burst1(root,name,source)
    row=ledger(root)['sources'].get(name)
    if row is None:return source,False
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed below-defense source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Ambiguous below-defense delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Below-defense historical source changed: '+name
    return source,True

def project_sources(root,sources=None):
    from portable_burst1_ally_source_contract import project_sources as project_burst1
    root=Path(root);sources,_=project_burst1(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed below-defense helper: '+name
    for name in data['sources']:sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()),burst1_projected=True)
    return sources,list(data['sources'])
