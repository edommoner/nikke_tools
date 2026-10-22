"""Reviewed physical reach source deltas; historical token fixtures remain exact."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-physical-interrupt-source-delta.json').read_text())
def baseline_event(root,source):
    for row in ledger(root)['event']:
        assert source.count(row['current'])==1,'Unreviewed physical interrupt macro statements'
        source=source.replace(row['current'],row['baseline'],1)
    return source

def baseline_phase(root,source):
    from portable_mode_capacity_source_contract import baseline_source
    source,_=baseline_source(root,'gpu/weapon_frame_phases.slang',source)
    row=ledger(root)['phase']
    assert source.count(row['current'])==1,'Weapon phase statements: unreviewed physical interrupt sampling hook'
    return source.replace(row['current'],row['baseline'],1)

def verify_sources(root,sources=None):
    root=Path(root);sources=sources or {};data=ledger(root)
    for name,digest in data['current'].items():
        raw=sources[name].encode() if name in sources else (root/name).read_bytes()
        from portable_mode_capacity_source_contract import baseline_source
        source,_=baseline_source(root,name,raw.decode())
        raw=source.encode()
        assert hashlib.sha256(raw).hexdigest()==digest,'Unreviewed physical interrupt source: '+name
    return list(data['current'])
