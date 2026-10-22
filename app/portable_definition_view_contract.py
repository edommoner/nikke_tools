"""Canonical wire accessors and all consumers stay fixed during view lowering."""
import hashlib,json,re
from pathlib import Path
from portable_weapon_phase_contract import tokens


def fingerprint(text):return hashlib.sha256(json.dumps(tokens(text),separators=(',',':')).encode()).hexdigest()


def verify(root,*,sources=None):
    root=Path(root);sources=sources or {}
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
    assert fingerprint(state[:start]+'DEFINITION_VIEW_SLOT'+state[end:])==f['event_without_definition_tokens'],'Event/state/consumer statements changed'
    begin=decoder.index('{',decoder.index('void loadDefinition'));finish=begin+1;depth=1
    while depth:
        depth+=(decoder[finish]=='{')-(decoder[finish]=='}');finish+=1
    assert tokens(decoder[begin:finish])==tokens('{ d._wireInput=input;d._wireRow=row;d._overrideMask=0;d._route=0;d._hits=0; }'),'Wire snapshot or override initialization changed'
    assert fingerprint(decoder[:begin]+'DEFINITION_LOADER_SLOT'+decoder[finish:])==f['decoder_without_loader_body_tokens'],'Canonical wire accessor/decoder changed'
    for name,digest in f['other_shared_sources'].items():
        raw=sources[name].encode('utf-8') if name in sources else (root/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==digest,'Shared numeric/consumer source changed: '+name
    # The fixed closure has indexed reads, never an escaped mutable command
    # buffer. Future source changes must deliberately re-audit this assumption.
    for name in ['gpu/event_runtime.slang','gpu/definition_runtime.slang',*f['other_shared_sources']]:
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
    return dict(verified=True,properties=55,local_override_properties=['damageRoute','damageHits'],wire_immutable=True,other_shared_sources_unchanged=True,gpu_calls=0,scope='Source correspondence/snapshot contract; GPU copy semantics and numerical parity require actual execution')
