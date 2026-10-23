"""Exact native-consumer/observation delta; historical calculation baselines stay anchored."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-query-diagnostic-source-delta.json').read_text())
def baseline_source(root,name,source,*,layout_projected=False):
    if not layout_projected:
        from portable_scratch_layout_source_contract import baseline_source as project_layout
        source,_=project_layout(root,name,source)
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed query diagnostic source: '+name
    for c in reversed(row['changes']):
        assert source.count(c['current'])==1,'Ambiguous query diagnostic delta: '+name
        source=source.replace(c['current'],c['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Query diagnostic baseline changed: '+name
    return source,True
def project_sources(root,sources=None,*,layout_projected=False):
    root=Path(root);sources=dict(sources or {})
    if not layout_projected:
        from portable_scratch_layout_source_contract import project_sources as project_layout
        sources,_=project_layout(root,sources)
    rows=ledger(root)['sources']
    for name in rows:sources[name],_=baseline_source(root,name,sources.get(name,(root/name).read_text()),layout_projected=True)
    return sources,list(rows)
