"""Exact reviewed HP skill delta; historical source ledgers are unchanged."""
import hashlib
import json
from pathlib import Path

def ledger(root):
    return json.loads((Path(root)/'tests/fixtures/portable-skill-hp-basis-source-delta.json').read_text())

def baseline_source(root, name, source):
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed HP skill source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Missing or ambiguous HP skill delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'HP skill historical source changed: '+name
    return source,True

def verify_sources(root,sources=None,*,pellet_projected=False):
    root=Path(root);sources=sources or {};data=ledger(root)
    if not pellet_projected:
        from portable_pellet_shot_source_contract import project_sources
        sources,_=project_sources(root,sources)
    for name in data['sources']:
        baseline_source(root,name,sources.get(name,(root/name).read_text()))
    for name,digest in data['new_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed HP skill helper: '+name
    return [*data['sources'],*data['new_sources']]
