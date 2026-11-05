"""Check canonical definition properties against the current wire declaration."""
import json
from pathlib import Path
from portable_weapon_phase_contract import tokens


def verify(root, *, sources=None):
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
    begin=decoder.index('{',decoder.index('void loadDefinition'));finish=begin+1;depth=1
    while depth:
        depth+=(decoder[finish]=='{')-(decoder[finish]=='}');finish+=1
    assert tokens(decoder[begin:finish])==tokens('{ d._wireInput=input;d._wireRow=row;d._overrideMask=0;d._route=0;d._hits=0; }'),'Wire snapshot or override initialization changed'
    return dict(verified=True, properties=len(f['fields']), local_override_properties=['damageRoute','damageHits'], gpu_calls=0)
