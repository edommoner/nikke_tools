"""One live typed/canonical geometry order for frame aims and physical shots."""
def live_rows(world,geom,spec):
    from calculator import aim,boss_pattern
    from portable_typed_geometry_specs import normalize
    if getattr(geom,'_nikke_typed_world',None) is not None:
        if geom._nikke_typed_world is not world:raise ValueError('Typed geometry belongs to another world')
        geom=geom._nikke_canonical_geometry
    literal=normalize(spec,len(world.bindings),int(world.bindings[0].handle.kind));rows=[];typed={};canonical={}
    for run in world.clock._runs:
        for j,target in enumerate(run.targets):canonical[target.spec.name]=(target.spec.z,run.start_t,run.p.idx,j,0)
    for target in geom.targets:
        if target.name not in canonical:raise ValueError('Canonical geometry lost its world identity')
        rows.append((canonical[target.name],target))
    for slot,(binding,shape) in enumerate(zip(world.bindings,literal['shapes'],strict=True)):
        target=world.targets.rows[slot]
        if target is None or not target.alive:continue
        if binding.label in canonical:raise ValueError('Typed and canonical target labels must be distinct')
        run=world.clock._runs[binding.node]
        if not run.active or run.opens!=target.handle.generation:raise ValueError('Typed geometry requires the owning live generation')
        sh=aim.Shape(**{k:shape[k] for k in ('x','y','r','w','h','rot')})
        g=boss_pattern.GeomTarget(binding.label,'typed_projectile' if int(target.handle.kind)==2 else 'typed_hp_shield',sh)
        rows.append(((shape['z'],run.start_t,binding.node,slot,1),g));typed[id(g)]=(slot,target.handle)
    rows.sort(key=lambda row:row[0],reverse=True)
    return rows,typed,geom
