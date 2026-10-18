"""Configured actor bindings shared by the reference and CUDA world adapters.

Ownership is descriptive: these rows never decide a skill's enemy-count policy.
Live generation and presence belong to the source lifecycle, not this table.
"""
from dataclasses import dataclass
import math
from impact_specs import ActorHandle,ActorKind

MAX_ACTORS=128
ACTOR_WORDS=8
BODY_SOURCE,PART_SOURCE,ADD_SOURCE=0,1,2

@dataclass(frozen=True)
class ActorBinding:
    kind:ActorKind
    identity:int
    label:str
    source:int
    run:int=-1
    slot:int=0
    parent:ActorHandle|None=None

def bindings(patterns):
    from calculator.boss_pattern import ADD_PREFIX
    body=ActorHandle(ActorKind.BODY,0)
    result=[ActorBinding(ActorKind.BODY,0,'__enemy__',BODY_SOURCE)]
    identities={ActorKind.PART:0,ActorKind.ADD:0}
    for run,p in enumerate(patterns):
        if p.kind=='parts':
            for slot,spec in enumerate(p.targets):
                identity=identities[ActorKind.PART];identities[ActorKind.PART]+=1
                result.append(ActorBinding(ActorKind.PART,identity,spec.name,PART_SOURCE,run,slot,body))
        if p.summon is not None:
            for slot in range(p.summon.count):
                identity=identities[ActorKind.ADD];identities[ActorKind.ADD]+=1
                result.append(ActorBinding(ActorKind.ADD,identity,f'{ADD_PREFIX}{p.id}#{slot+1}',ADD_SOURCE,run,slot))
    return tuple(result)

def packed_bindings(patterns,live_indices):
    count=1+sum(len(p.targets) if p.kind=='parts' else 0 for p in patterns)+sum(p.summon.count if p.summon is not None else 0 for p in patterns)
    if count>MAX_ACTORS:raise ValueError('World actor capacity exceeded')
    return pack_rows(bindings(patterns),live_indices)

def pack_rows(rows,live_indices):
    rows=sorted(rows,key=lambda b:(int(b.kind),b.identity))
    if len(rows)>MAX_ACTORS:raise ValueError('World actor capacity exceeded')
    out=[0.0]*(1+MAX_ACTORS*ACTOR_WORDS);out[0]=len(rows)
    for index,b in enumerate(rows):
        run=-1 if b.run<0 else live_indices.get(b.run,-1)
        # Only authored fixed parts can currently use the static part pool.
        # Other lifecycles must be connected before their rows can be admitted.
        if b.source==PART_SOURCE and run>=0:raise ValueError('Dynamic part lifecycle is not connected')
        row=[int(b.kind),b.identity,b.source,run,b.slot,int(b.parent.kind) if b.parent else -1,b.parent.identity if b.parent else -1,0]
        start=1+index*ACTOR_WORDS;out[start:start+ACTOR_WORDS]=row
    validate_bindings(out)
    return out

def validate_bindings(values):
    if len(values)!=1+MAX_ACTORS*ACTOR_WORDS or any(type(v) not in (int,float) or not math.isfinite(v) or int(v)!=v for v in values):raise ValueError('Invalid world actor table')
    count=int(values[0])
    if not 1<=count<=MAX_ACTORS:raise ValueError('Invalid world actor count')
    seen=set();previous=(-1,-1);add_identity=0
    for index in range(count):
        kind,identity,source,run,slot,parent_kind,parent_id,reserved=map(int,values[1+index*ACTOR_WORDS:1+(index+1)*ACTOR_WORDS])
        key=(kind,identity)
        if key<=previous:raise ValueError('World actor bindings must be in canonical order')
        previous=key
        if index==0 and source!=BODY_SOURCE:raise ValueError('World body must be the first binding')
        if key in seen or identity<0 or identity>=2**28 or slot<0 or reserved:raise ValueError('Invalid world actor identity')
        if source==BODY_SOURCE:
            if index!=0 or (kind,identity,run,slot,parent_kind,parent_id)!=(0,0,-1,0,-1,-1):raise ValueError('Invalid world body binding')
        elif source==PART_SOURCE:
            if kind!=1 or run!=-1 or slot>=32 or identity!=slot or (parent_kind,parent_id)!=(0,0):raise ValueError('Invalid fixed part binding')
        elif source==ADD_SOURCE:
            if kind!=5 or identity!=add_identity or not 0<=run<32 or (parent_kind,parent_id)!=(-1,-1):raise ValueError('Invalid summon binding')
            add_identity+=1
        else:raise ValueError('Unknown world actor source')
        seen.add(key)
    if any(values[1+count*ACTOR_WORDS:]):raise ValueError('Nonzero unused world actor rows')

def empty_bindings(part_count=0):
    if type(part_count) is not int or not 0<=part_count<=32:raise ValueError('Invalid fixed actor count')
    rows=list(bindings([]));body=ActorHandle(ActorKind.BODY,0)
    rows.extend(ActorBinding(ActorKind.PART,i,f'fixed#{i}',PART_SOURCE,slot=i,parent=body) for i in range(part_count))
    return pack_rows(rows,{})
