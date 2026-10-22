"""Canonical wire accessors and consumers outside the exact reviewed scope delta."""
import hashlib,json,re
from pathlib import Path
from portable_weapon_phase_contract import tokens


def fingerprint(text):return hashlib.sha256(json.dumps(tokens(text),separators=(',',':')).encode()).hexdigest()


def verify(root,*,sources=None):
    root=Path(root);sources=sources or {}
    from portable_undying_predicate_source_contract import project_sources as project_undying
    sources,undying_deltas=project_undying(root,sources)
    from portable_ally_random_source_contract import ledger as allied_ledger
    allied_deltas=list(allied_ledger(root)['sources'])
    from portable_accuracy_predicate_source_contract import project_sources as project_accuracy
    sources,accuracy_deltas=project_accuracy(root,sources,undying_projected=True)
    from portable_manual_swap_source_contract import project_sources as project_manual
    sources,manual_swap_deltas=project_manual(root,sources,accuracy_projected=True)
    from portable_ammo_equivalent_source_contract import project_sources as project_ammo
    sources,ammo_equivalent_deltas=project_ammo(root,sources,manual_projected=True)
    from portable_pellet_shot_source_contract import project_sources
    sources,pellet_shot_deltas=project_sources(root,sources,ammo_projected=True)
    def read(name):return sources.get(name,(root/name).read_text(encoding='utf-8'))
    f=json.loads((root/'tests/fixtures/portable-definition-view.json').read_text())
    state=read('gpu/event_runtime.slang');decoder=read('gpu/definition_runtime.slang')
    start=state.index('struct Definition');end=state.index('\n};',start)+3
    expected=['struct Definition { uint _wireInput,_wireRow,_overrideMask,_route,_hits;']
    for field in f['fields']:
        kind,name,accessor=(field[k] for k in ('type','name','accessor'))
        getter=accessor+'(_wireInput,_wireRow)'
        if name in ('damageRoute','damageHits'):
            slot,bit=('_route',1) if name=='damageRoute' else ('_hits',2)
            expected.append(f'property {kind} {name} {{ get {{ return (_overrideMask&{bit}U)!=0 ? {slot} : {getter}; }} set {{ {slot}=newValue; _overrideMask|={bit}U; }} }}')
        else:expected.append(f'property {kind} {name} {{ get {{ return {getter}; }} }}')
    expected.append('};')
    assert len(f['fields'])==len({r['name'] for r in f['fields']})==55,'Canonical55 fields missing'
    assert tokens(state[start:end])==tokens('\n'.join(expected)),'Definition property/type/override mapping changed'
    # Only explicit local Frame metadata is added. Runtime/wire and every
    # other statement retain the historical token proof.
    frame_old='uint64_t skillCritRate;'
    frame_new='uint64_t skillCritRate,interruptAmount;\n    uint interruptReach;'
    assert state.count(frame_new)==1,'Unreviewed interrupt Frame metadata'
    from portable_physical_interrupt_contract import baseline_event,verify_sources
    physical_deltas=verify_sources(root,sources,pellet_projected=True)
    from portable_skill_hp_basis_source_contract import baseline_source as baseline_hp_event
    state,_=baseline_hp_event(root,'gpu/event_runtime.slang',state)
    state_baseline=baseline_event(root,state.replace(frame_new,frame_old,1))
    bstart=state_baseline.index('struct Definition');bend=state_baseline.index('\n};',bstart)+3
    assert fingerprint(state_baseline[:bstart]+'DEFINITION_VIEW_SLOT'+state_baseline[bend:])==f['event_without_definition_tokens'],'Event/state/consumer statements changed'
    begin=decoder.index('{',decoder.index('void loadDefinition'));finish=begin+1;depth=1
    while depth:
        depth+=(decoder[finish]=='{')-(decoder[finish]=='}');finish+=1
    assert tokens(decoder[begin:finish])==tokens('{ d._wireInput=input;d._wireRow=row;d._overrideMask=0;d._route=0;d._hits=0; }'),'Wire snapshot or override initialization changed'
    assert fingerprint(decoder[:begin]+'DEFINITION_LOADER_SLOT'+decoder[finish:])==f['decoder_without_loader_body_tokens'],'Canonical wire accessor/decoder changed'
    reviewed_deltas=[];factor_deltas=[];part_deltas=[];interrupt_deltas=[];reach_deltas=[]
    reach=json.loads((root/'tests/fixtures/portable-interrupt-reach-source-delta.json').read_text())
    parts=json.loads((root/'tests/fixtures/portable-parts-source-delta.json').read_text())
    interrupts=json.loads((root/'tests/fixtures/portable-interrupt-source-delta.json').read_text())
    capacity_deltas=[]
    from portable_lost_hp_attack_source_contract import baseline_source as baseline_lost_hp,verify_sources as verify_lost_hp
    lost_hp_deltas=verify_lost_hp(root,sources)
    from portable_skill_hp_basis_source_contract import baseline_source as baseline_hp_basis,verify_sources as verify_hp_basis
    hp_basis_deltas=verify_hp_basis(root,sources,pellet_projected=True)
    from portable_mode_capacity_source_contract import baseline_source as baseline_capacity
    ally_burst_deltas=[]
    from portable_ally_burst_source_contract import baseline_source as baseline_ally_burst
    for name,digest in f['other_shared_sources'].items():
        raw=sources[name].encode('utf-8') if name in sources else (root/name).read_bytes()
        baseline,applied=baseline_lost_hp(root,name,raw.decode('utf-8'))
        if applied:raw=baseline.encode('utf-8')
        baseline,applied=baseline_hp_basis(root,name,raw.decode('utf-8'))
        if applied:raw=baseline.encode('utf-8')
        if name!='gpu/weapon_frame_phases.slang':
            baseline,applied=baseline_capacity(root,name,raw.decode('utf-8'))
            if applied:raw=baseline.encode('utf-8');capacity_deltas.append(name)
        baseline,applied=baseline_ally_burst(root,name,raw.decode('utf-8'))
        if applied:raw=baseline.encode('utf-8');ally_burst_deltas.append(name)
        if name=='gpu/world_actor_state.slang' and hashlib.sha256(raw).hexdigest()!=digest:
            from portable_query_boundary_contract import baseline_scope_source
            baseline,applied=baseline_scope_source(raw.decode('utf-8'))
            assert applied,'Shared consumer change is not the reviewed scope snapshot delta'
            raw=baseline.encode('utf-8');reviewed_deltas.append(name)
        if name=='gpu/damage_runtime.slang' and hashlib.sha256(raw).hexdigest()!=digest:
            # Deliberate later feature work, not a claim that the old consumer
            # bytes survived. Retain its baseline hash and admit only this exact
            # reviewed extraction. Numerical parity still requires GPU evidence.
            assert digest=='4cd960b9b0d3bd42490e71794ae60077095d41a0c1ca9b88312aad389468170f'
            assert reach['baseline'][name]=='7f7b7a24887be9361bea9ad360e99db0ab4323ede760cc0070ea1c7262feca5f'
            assert hashlib.sha256(raw).hexdigest()==reach['current'][name],'Unreviewed damage factor source'
            reach_deltas.append(name)
            assert hashlib.sha256(read('gpu/damage_factors.slang').encode('utf-8')).hexdigest()=='c806441d5532ccc494e3f9099033378621e95cc248fe1be8826f9864de2ca3de','Unreviewed damage factor product'
            factor_deltas=['gpu/damage_runtime.slang','gpu/damage_factors.slang']
        elif name=='gpu/weapon_frame_phases.slang' and hashlib.sha256(raw).hexdigest()!=digest:
            from portable_physical_interrupt_contract import baseline_phase,ledger
            assert ledger(root)['baseline'][name]==digest,'Physical hook ledger changed historical weapon baseline'
            baseline=baseline_phase(root,raw.decode(),pellet_projected=True).encode();capacity_deltas.append(name)
            assert hashlib.sha256(baseline).hexdigest()==digest,'Weapon statements outside physical hook changed'
        elif name in reach['current'] and hashlib.sha256(raw).hexdigest()!=digest:
            assert reach['baseline'][name]==digest,'Interrupt reach ledger changed historical baseline'
            assert hashlib.sha256(raw).hexdigest()==reach['current'][name],'Unreviewed interrupt reach source: '+name
            reach_deltas.append(name)
        elif name in interrupts['current'] and hashlib.sha256(raw).hexdigest()!=digest:
            assert interrupts['baseline'][name]==digest,'Interrupt source ledger changed historical baseline'
            assert hashlib.sha256(raw).hexdigest()==interrupts['current'][name],'Unreviewed interrupt source: '+name
            interrupt_deltas.append(name)
        elif name in parts['current'] and hashlib.sha256(raw).hexdigest()!=digest:
            assert parts['baseline'][name]==digest,'Part source ledger changed historical baseline'
            assert hashlib.sha256(raw).hexdigest()==parts['current'][name],'Unreviewed part receipt source: '+name
            part_deltas.append(name)
        else:
            assert hashlib.sha256(raw).hexdigest()==digest,'Shared numeric/consumer source changed: '+name
    assert set(reach_deltas)==set(reach['current']),'Partial interrupt reach ledger'
    for name,digest in reach['new_sources'].items():
        assert hashlib.sha256(read(name).encode('utf-8')).hexdigest()==digest,'Unreviewed interrupt reach helper'
        reach_deltas.append(name)
    if interrupt_deltas:assert set(interrupt_deltas)==set(interrupts['current']),'Partial interrupt source ledger'
    if part_deltas:
        assert set(part_deltas)==set(parts['current']),'Partial part receipt source ledger'
        for name,digest in parts['new_sources'].items():
            assert hashlib.sha256(read(name).encode('utf-8')).hexdigest()==digest,'Unreviewed part receipt codec'
            part_deltas.append(name)
    # The fixed closure has indexed reads, never an escaped mutable command
    # buffer. Future source changes must deliberately re-audit this assumption.
    for name in ['gpu/event_runtime.slang','gpu/definition_runtime.slang',*f['other_shared_sources'],*factor_deltas,*part_deltas,*reach_deltas,*hp_basis_deltas,*pellet_shot_deltas,*ammo_equivalent_deltas,*manual_swap_deltas]:
        ts=tokens(read(name))
        for i,t in enumerate(ts):
            if t!='commands':continue
            assert ts[i+1] in ('[',';'),'Input buffer escaped as mutable argument: '+name
            if ts[i+1]!='[':continue
            depth=1;j=i+2
            while depth:
                depth+=(ts[j]=='[')-(ts[j]==']');j+=1
            assert ts[j]!='=' or ts[j+1]=='=','Input command write: '+name
            assert ts[j] not in ('+','-','|','&','^','*','/','%') or ts[j+1]!='=','Input compound command write: '+name
            assert ts[j:j+2] not in (['+','+'],['-','-']),'Input command increment: '+name
    return dict(verified=True,properties=55,local_override_properties=['damageRoute','damageHits'],wire_immutable=True,other_shared_sources_unchanged=not (allied_deltas or undying_deltas or accuracy_deltas or reviewed_deltas or factor_deltas or part_deltas or interrupt_deltas or ally_burst_deltas or capacity_deltas or pellet_shot_deltas or ammo_equivalent_deltas or manual_swap_deltas),other_sources_outside_reviewed_delta_unchanged=True,reviewed_scope_snapshot_sources=reviewed_deltas,reviewed_damage_factor_sources=factor_deltas,reviewed_part_receipt_sources=part_deltas,reviewed_interrupt_sources=interrupt_deltas,reviewed_interrupt_reach_sources=reach_deltas,reviewed_interrupt_frame_metadata=True,reviewed_physical_interrupt_sources=physical_deltas,reviewed_ally_burst_sources=ally_burst_deltas,reviewed_mode_capacity_sources=capacity_deltas,reviewed_skill_hp_basis_sources=hp_basis_deltas,reviewed_lost_hp_attack_sources=lost_hp_deltas,reviewed_pellet_shot_sources=pellet_shot_deltas,reviewed_ammo_equivalent_sources=ammo_equivalent_deltas,reviewed_manual_swap_sources=manual_swap_deltas,reviewed_accuracy_predicate_sources=accuracy_deltas,reviewed_undying_predicate_sources=undying_deltas,reviewed_ally_random_sources=allied_deltas,gpu_calls=0,scope='Source correspondence/snapshot contract; explicit later source deltas do not prove numerical parity, which requires actual execution')
