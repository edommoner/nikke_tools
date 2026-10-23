"""Reviewed physical reach source deltas; historical token fixtures remain exact."""
import hashlib,json
from pathlib import Path

def ledger(root):return json.loads((Path(root)/'tests/fixtures/portable-physical-interrupt-source-delta.json').read_text())
def baseline_event(root,source):
    for row in ledger(root)['event']:
        assert source.count(row['current'])==1,'Unreviewed physical interrupt macro statements'
        source=source.replace(row['current'],row['baseline'],1)
    return source

def baseline_phase(root,source,*,pellet_projected=False):
    if not pellet_projected:
        from portable_manual_swap_source_contract import baseline_source as baseline_manual
        source,_=baseline_manual(root,'gpu/weapon_frame_phases.slang',source)
        from portable_pellet_shot_source_contract import baseline_source as baseline_pellet_shot
        source,_=baseline_pellet_shot(root,'gpu/weapon_frame_phases.slang',source)
    from portable_mode_capacity_source_contract import baseline_source
    source,_=baseline_source(root,'gpu/weapon_frame_phases.slang',source)
    row=ledger(root)['phase']
    assert source.count(row['current'])==1,'Weapon phase statements: unreviewed physical interrupt sampling hook'
    return source.replace(row['current'],row['baseline'],1)

def verify_sources(root,sources=None,*,pellet_projected=False):
    root=Path(root);sources=sources or {};data=ledger(root)
    for name,digest in data['current'].items():
        raw=sources[name].encode() if name in sources else (root/name).read_bytes()
        if not pellet_projected:
            from portable_interrupt_aim_source_contract import baseline_source as project_interrupt
            source,_=project_interrupt(root,name,raw.decode());raw=source.encode()
            from portable_manual_swap_source_contract import baseline_source as baseline_manual
            source,_=baseline_manual(root,name,raw.decode());raw=source.encode()
            from portable_ammo_equivalent_source_contract import baseline_source as baseline_ammo
            source,_=baseline_ammo(root,name,raw.decode());raw=source.encode()
            from portable_pellet_shot_source_contract import baseline_source as baseline_pellet_shot
            source,_=baseline_pellet_shot(root,name,raw.decode());raw=source.encode()
        from portable_skill_hp_basis_source_contract import baseline_source as baseline_hp_basis
        source,_=baseline_hp_basis(root,name,raw.decode())
        raw=source.encode()
        from portable_mode_capacity_source_contract import baseline_source
        source,_=baseline_source(root,name,raw.decode())
        raw=source.encode()
        assert hashlib.sha256(raw).hexdigest()==digest,'Unreviewed physical interrupt source: '+name
    return list(data['current'])
