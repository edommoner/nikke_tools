"""Finite ATK/DEF admission delta; shared scalar arithmetic is unchanged."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-lost-hp-attack-source-delta.json').read_text())
def baseline_source(root,name,source):
    rows=ledger(root)['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed lost-HP admission source: '+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Missing or ambiguous lost-HP delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Lost-HP historical source changed: '+name
    return source,True
def verify_sources(root,sources=None):
    root=Path(root);sources=sources or {}
    for name in ledger(root)['sources']:baseline_source(root,name,sources.get(name,(root/name).read_text()))
    return list(ledger(root)['sources'])
