"""Exact context/state delta above the previous verified shared runtime."""
import hashlib,json
from pathlib import Path


def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-not-core-source-delta.json').read_text())


def baseline_source(root,name,source,*,duration_projected=False):
    if not duration_projected:
        from portable_duration_scaling_source_contract import baseline_source as project_duration
        source,_=project_duration(root,name,source)
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name];assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed not-core source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Ambiguous not-core delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Not-core baseline changed: '+name
    return source,True


def project_sources(root,sources=None):
    from portable_duration_scaling_source_contract import project_sources as project_duration
    root=Path(root);sources,_=project_duration(root,sources);data=ledger(root)
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed not-core helper: '+name
    for name in data['sources']:sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()),duration_projected=True)
    return sources,list(data['sources'])
