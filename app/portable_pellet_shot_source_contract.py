"""Finite per-shot notification hooks, projected before historical ledgers."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-pellet-shot-source-delta.json').read_text())
def baseline_source(root,name,source):
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed per-shot source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Missing or ambiguous per-shot delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Per-shot historical source changed: '+name
    return source,True

def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {});data=ledger(root)
    for name in data['sources']:
        sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()))
    for name,digest in data['new_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed per-shot helper: '+name
    return sources,[*data['sources'],*data['new_sources']]
