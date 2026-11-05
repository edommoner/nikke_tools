"""Preserve baseline query tokens plus the reviewed scalar-snapshot correction."""
import hashlib,json,re
from pathlib import Path
from portable_weapon_phase_contract import tokens


HELPER='''[noinline]
uint actorStateQueryScopeSnapshot(uint at)
{ return results[at]; }'''
OLD='uint at=actorFieldHead(s)+3,previous=results[at];results[at]=actorFieldLogicalSlot(s,target)+1;return previous;'
NEW='uint at=actorFieldHead(s)+3;uint previous=actorStateQueryScopeSnapshot(at);results[at]=actorFieldLogicalSlot(s,target)+1;return previous;'

SCOPE_COMMENT='// Preserve the scalar value before updating the same RW buffer element.\n// Slang CUDA can otherwise retain a pointer and load it after the store.\n'

def baseline_scope_source(source):
    if 'actorStateQueryScopeSnapshot' not in tokens(source):return source,False
    helper=SCOPE_COMMENT+HELPER+'\n'
    assert source.count(helper)==1,'Original query statements: unexpected complete scope snapshot helper'
    assert source.count(NEW)==1,'Original query statements: unexpected scope snapshot use'
    return source.replace(helper,'',1).replace(NEW,OLD,1),True


def reviewed_scope_delta(actual):
    helper=tokens(HELPER);new=tokens(NEW)
    def positions(needle):return [i for i in range(len(actual)-len(needle)+1) if actual[i:i+len(needle)]==needle]
    at=positions(helper)
    assert len(at)==1,'Original query statements: unexpected scope snapshot helper'
    del actual[at[0]:at[0]+len(helper)]
    at=positions(new)
    assert len(at)==1,'Original query statements: unexpected scope snapshot call/store/return'
    actual[at[0]:at[0]+len(new)]=tokens(OLD)
    return actual

def baseline_interrupt_pool_source(source):
    changes=[('if(kind==1||kind==6 ? mode!=1 : mode<2||mode>4)','if(kind==1 ? mode!=1 : mode<2||mode>4)'),
             ('kind!=1 && kind!=6 && (n!=0||commands[d+8]!=0)','kind!=1 && (n!=0||commands[d+8]!=0)')]
    if not any(new in source for new,_ in changes):return source,False
    for new,old in changes:
        assert source.count(new)==1,'Original query statements: unexpected interrupt pool admission delta'
        source=source.replace(new,old,1)
    return source,True

def baseline_interrupt_field_source(source):
    added='if(commands[b]==6) { for(uint i=0;i<12;i++) results[out+i]=0;results[out]=1; }\n            else '
    if added not in source:return source,False
    assert source.count(added)==1,'Original query statements: unexpected private interrupt numeric view'
    return source.replace(added,'',1),True


def verify(root,*,sources=None):
    root=Path(root);fixture=json.loads((root/'tests/fixtures/portable-query-boundaries.json').read_text());names=[];scope_delta=False;interrupt_delta=False;interrupt_field_delta=False
    capacity_deltas=[]
    # The new live-ammunition source has an exact full-file inverse. Apply it
    # before the older per-file query chain, keeping the original token hashes.
    from portable_parent_fixed_source_contract import project_sources as project_parent
    try:sources=project_parent(root,sources)
    except AssertionError as error:raise AssertionError('Original query statements/signatures/macros changed') from error
    from portable_mode_capacity_source_contract import baseline_source as baseline_capacity
    for row in fixture['files']:
        source=(sources or {}).get(row['path'],(root/row['path']).read_text())
        from portable_skill_hp_basis_source_contract import baseline_source as baseline_hp_basis
        try:
            from portable_native_query_source_contract import baseline_source as baseline_native
            source,_=baseline_native(root,row['path'],source)
            from portable_state_focus_source_contract import baseline_source as baseline_focus
            source,_=baseline_focus(root,row['path'],source)
            from portable_ally_random_source_contract import baseline_source as baseline_allied
            source,_=baseline_allied(root,row['path'],source)
            from portable_undying_predicate_source_contract import baseline_source as baseline_undying
            source,_=baseline_undying(root,row['path'],source)
            from portable_accuracy_predicate_source_contract import baseline_source as baseline_accuracy
            source,_=baseline_accuracy(root,row['path'],source)
            from portable_manual_swap_source_contract import baseline_source as baseline_manual
            source,_=baseline_manual(root,row['path'],source)
            from portable_ammo_equivalent_source_contract import baseline_source as baseline_ammo
            source,_=baseline_ammo(root,row['path'],source)
            source,_=baseline_hp_basis(root,row['path'],source)
            source,capacity_delta=baseline_capacity(root,row['path'],source)
        except AssertionError as error:raise AssertionError('Original query statements/signatures/macros changed: '+row['path']) from error
        if capacity_delta:capacity_deltas.append(row['path'])
        if row['path']=='gpu/world_actor_pools.slang':source,interrupt_delta=baseline_interrupt_pool_source(source)
        if row['path']=='gpu/world_actor_fields.slang':source,interrupt_field_delta=baseline_interrupt_field_source(source)
        for name in row['functions']:
            pattern=r'(?m)^\[noinline\]\n(?=(?:bool|uint|uint64_t) '+re.escape(name)+r'\()'
            source,count=re.subn(pattern,'',source)
            assert count==1,'Query boundary missing or duplicated: '+name
            names.append(name)
        actual=tokens(source)
        if row['path']=='gpu/world_actor_state.slang' and 'actorStateQueryScopeSnapshot' in actual:
            actual=reviewed_scope_delta(actual);scope_delta=True
        assert len(actual)==row['token_count'] and hashlib.sha256(json.dumps(actual,separators=(',',':')).encode()).hexdigest()==row['token_sha256'],'Original query statements/signatures/macros changed: '+row['path']
    assert len(names)==6 and len(set(names))==6
    return dict(verified=True,baseline_commit=fixture['baseline_commit'],functions=names,files=len(fixture['files']),original_file_tokens_preserved=not (scope_delta or interrupt_delta or interrupt_field_delta or capacity_deltas),unmodified_tokens_preserved=True,explicit_scope_snapshot_delta=scope_delta,explicit_interrupt_pool_delta=interrupt_delta,explicit_interrupt_field_delta=interrupt_field_delta,explicit_mode_capacity_delta=bool(capacity_deltas),reviewed_mode_capacity_sources=capacity_deltas,explicit_max_ammo_scaling_delta=True,gpu_calls=0,scope='Six noinline boundaries and exact reviewed scalar snapshot/private interrupt admission/view/mode capacity deltas; baseline token hashes unchanged')
