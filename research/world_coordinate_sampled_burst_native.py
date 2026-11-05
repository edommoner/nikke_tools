"""Passively retain queue birth order and actual legacy calculations."""
import sys

def observe(case):
    import engine_worker
    from calculator import timeline
    from world_coordinate_sampled_skill_native import observe as parent
    from world_full_burst_landing_native import capture
    from world_frame_native import roster_names
    legacy_code=timeline.BurstController._fire_pending_burst_dmg.__code__
    names=roster_names(case);births=[];batches=[];legacy=[];order=[];previous=sys.getprofile()
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        name=frame.f_code.co_name
        if name=='_handle_damage_eff' and event=='return':
            v=frame.f_locals
            controller=v.get('burst_ctrl')
            if controller is not None:
                for mode,key,queue in ((1,'eff_with_coeff',controller._pending_burst_dmg),(2,'pending_eff',controller._pending_landing_dmg)):
                    eff=v.get(key)
                    found=[entry for entry in queue if entry[1] is eff]
                    if len(found)==1:
                        owner=found[0][0];hits=found[0][2] if mode==1 else eff['_latched_hit_count']
                        assert all(row['_id']!=id(eff) for row in births),'Queue birth observed twice'
                        births.append(dict(_id=id(eff),_effect=eff,mode=mode,name=eff['name'],owner=names.index(owner),created=v['t'],hits=hits,consumed=False))
        if frame.f_code is legacy_code and event=='call':
            v=frame.f_locals
            batch=[row for row in births if not row['consumed']];batches.append(dict(time=v['t'],entries=[{k:x for k,x in row.items() if not k.startswith('_') and k!='consumed'} for row in batch]))
            for row in batch:row['_batch']=len(batches)-1;row['_index']=batch.index(row);row['consumed']=True
        caller=frame.f_back
        if event=='return' and frame.f_code is timeline.calc_damage.__code__ and caller is not None and (caller.f_code is legacy_code or caller.f_code.co_name=='_handle_damage_eff'):
            c=caller.f_locals;order.append(dict(queue='legacy' if caller.f_code is legacy_code else 'ordinary',name=c['eff']['name'],time=c['t']))
        if event=='return' and frame.f_code is timeline.calc_damage.__code__ and caller is not None and caller.f_code is legacy_code:
            v=frame.f_locals
            c=caller.f_locals;eff=c['eff'];matches=[row for row in births if row['_id']==id(eff)];assert len(matches)==1
            row=matches[0];buffs=v['buffs'];legacy.append(dict(batch=row['_batch'],index=row['_index'],owner=row['owner'],name=eff['name'],time=c['t'],hit=int(c['_'])+1,hits=int(c['hit_count']),damage=answer['damage'],critical=answer['is_crit'],crit_fraction=answer['crit_frac'],crit_rate=buffs.get('crit_rate_skill',buffs.get('crit_rate',.15)),atk_pct=buffs.get('atk_pct',0)))
    sys.setprofile(profile)
    try:
        with capture(names) as full:n,t=parent(case)
    finally:sys.setprofile(previous)
    n.update(sampled_burst_batches=batches,sampled_legacy_damage=legacy,sampled_burst_calculation_order=order,full_burst_landing_observation=full)
    return n,t
