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


def verify(root,*,sources=None):
    root=Path(root);fixture=json.loads((root/'tests/fixtures/portable-query-boundaries.json').read_text());names=[];scope_delta=False
    for row in fixture['files']:
        source=(sources or {}).get(row['path'],(root/row['path']).read_text())
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
    return dict(verified=True,baseline_commit=fixture['baseline_commit'],functions=names,files=len(fixture['files']),original_file_tokens_preserved=not scope_delta,unmodified_tokens_preserved=True,explicit_scope_snapshot_delta=scope_delta,gpu_calls=0,scope='Six noinline boundaries and only the exact reviewed scalar snapshot delta; baseline token hashes unchanged')
