"""Explicit frozen-slot delivery policy; not a claim about game retargeting."""
from dataclasses import dataclass
from impact_specs import ActorHandle
from named_generation_locks import LockSnapshot,MAX_REVISION
from world_actor_runtime import ActorSnapshot

MODEL='cycle-frozen-slot-v1'
CAPACITY=128
READY,EMPTY,MISSING,STALE,DEAD=range(5)

@dataclass(frozen=True)
class Selection:
    status:int
    index:int
    handle:ActorHandle|None
    current_generation:int

def select(snapshot,hit,hits,views,*,model):
    if model!=MODEL or not isinstance(snapshot,LockSnapshot):raise ValueError('Explicit frozen-slot delivery model required')
    if type(snapshot.revision) is not int or not 0<=snapshot.revision<=MAX_REVISION:raise ValueError('Invalid snapshot revision')
    if type(hit) is not int or type(hits) is not int or not 1<=hit<=hits<=256:raise ValueError('Invalid bounded hit ordinal')
    handles=tuple(snapshot.handles);rows=tuple(views)
    if len(handles)>CAPACITY or len(rows)>CAPACITY:raise ValueError('Frozen delivery actor capacity exceeded')
    keys=set()
    for handle in handles:
        if not isinstance(handle,ActorHandle) or (handle.kind,handle.identity) in keys:raise ValueError('Invalid or duplicate frozen identity')
        keys.add((handle.kind,handle.identity))
    current={}
    for row in rows:
        if not isinstance(row,ActorSnapshot):raise ValueError('Invalid current actor view')
        key=(row.handle.kind,row.handle.identity)
        if key in current:raise ValueError('Duplicate current identity')
        current[key]=row
    if not handles:return Selection(EMPTY,0xffffffff,None,0)
    index=(hit-1)%len(handles);handle=handles[index]
    row=current.get((handle.kind,handle.identity))
    if row is None:return Selection(MISSING,index,handle,0)
    if row.handle.generation!=handle.generation:return Selection(STALE,index,handle,row.handle.generation)
    return Selection(READY if row.alive else DEAD,index,handle,row.handle.generation)
