"""Passive geometry/selection observation layered on the existing native bridge."""
import dataclasses,sys,types
from calculator import timeline
from calculator.boss_pattern import BossScript
from world_parts_skill_native import observe as original

def observe(case):
    codes=[c for c in timeline.simulate.__code__.co_consts if isinstance(c,types.CodeType) and c.co_name=='_coord_skill_hits']
    if len(codes)!=1:raise ValueError('Unique native coordinate skill selector required')
    previous=sys.getprofile();selections=[];snapshots=[];last=[None,None];errors=[];reuse=[True];reuse_checks=[0];pending={};accounting=[]
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        try:
            if frame.f_code is BossScript.hit_target.__code__:
                v=frame.f_locals;ev=v['ev'];boss=v['self']
                if ev.skill_name=='parts-source':
                    candidates=[(run,x) for run in boss._runs for x in run.targets if x.spec.name==ev.target]
                    run,x=candidates[0]
                    if event=='call':pending[id(frame)]=(bool(run.active and not x.destroyed),x.dealt,x.hits)
                    elif event=='return':
                        alive,dealt,hits=pending.pop(id(frame));accounting.append(dict(target=ev.target,time=v['t'],kind=answer,before_alive=alive,after_alive=bool(run.active and not x.destroyed),pool_damage_delta=x.dealt-dealt,pool_hits_delta=x.hits-hits))
            if event!='return':return

            v=frame.f_locals
            if frame.f_code is codes[0] and v['eff'].get('name')=='parts-source':
                g=v['geom'];selections.append(dict(time=v['t'],owner=v['cs'].name,targets=[e.target for e in answer],geometry=[t.name for t in g.targets],shapes=[dataclasses.asdict(t.shape) for t in g.targets],kinds=[t.kind for t in g.targets],auto_aim=list(g.auto_aim)))
            elif frame.f_code is BossScript._apply_geom.__code__:
                g=v['self'].geom
                if g is None:return
                row=dict(targets=[t.name for t in g.targets],shapes=[dataclasses.asdict(t.shape) for t in g.targets],kinds=[t.kind for t in g.targets],auto_aim=list(g.auto_aim),core=dataclasses.asdict(g.core) if g.core is not None else None)
                if last[0]==row:reuse[0]&=last[1] is g;reuse_checks[0]+=1
                else:snapshots.append(row)
                last[:]=[row,g]
        except (KeyError,AttributeError,TypeError,ValueError) as error:errors.append(type(error).__name__+': '+str(error))
    sys.setprofile(profile)
    try:native,trace=original(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Coordinate observation failed: '+str(errors))
    native['coordinate_skill']=dict(target_accounting=accounting,selections=selections,snapshots=snapshots,unchanged_geometry_reused=bool(reuse[0]),reuse_checks=reuse_checks[0])
    return native,trace
