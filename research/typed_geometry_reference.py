"""Point selection over the actual typed world's live states and shared shape math."""
from portable_typed_geometry_specs import normalize
from coordinate_geometry_reference import evaluate

def select(world,spec,kind):
    data=normalize(spec,len(world.bindings),kind);candidates=[]
    if world.last is None or world.finished:return None
    for slot,(binding,shape) in enumerate(zip(world.bindings,data['shapes'],strict=True)):
        target=world.targets.rows[slot]
        if target is None or not target.alive or int(target.handle.kind)!=kind:continue
        if kind==3 and (target.owner is None or (int(target.owner.kind),target.owner.identity,target.owner.generation)!=(0,0,1)):continue
        values=[shape[k] for k in ('kind','x','y','r','w','h','rot')]+data['point']+[0.,data['grow']]
        if not evaluate(values)['contains']:continue
        run=world.clock._runs[binding.node]
        if not run.active or run.opens!=target.handle.generation:raise ValueError('Typed geometry must read the owning live generation')
        candidates.append(((shape['z'],run.start_t,binding.node,slot),slot,target.handle))
    if not candidates:return None
    _,slot,handle=max(candidates,key=lambda row:row[0]);return slot,handle
