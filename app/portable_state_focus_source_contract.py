"""Cover/camera predicates and presence-driven aim source delta."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-state-focus-source-delta.json').read_text())
def baseline_source(root,name,source):
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed state-focus source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Missing or ambiguous state-focus delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'State/focus historical source changed: '+name
    return source,True
def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {});data=ledger(root)
    for name in data['sources']:sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()))
    return sources,list(data['sources'])
