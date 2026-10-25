"""Passive real landing capture, including native routing weights and boss gates."""
import sys,types
from world_coordinate_group_native import observe as grouped
from world_frame_native import roster_names

def observe(case):
    previous=sys.getprofile();codes=set();packets=[];errors=[];names=roster_names(case)
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='call':return
        if frame.f_code.co_name=='simulate':
            found=[c for c in frame.f_code.co_consts if isinstance(c,types.CodeType) and c.co_name=='_apply_lifesteal']
            if len(found)==1:codes.add(found[0])
        if frame.f_code not in codes:return
        try:
            v=frame.f_locals;ev=v['ev'];caller=frame.f_back
            while caller is not None and caller.f_code.co_name!='_land':caller=caller.f_back
            if caller is None:raise ValueError('Canonical landing parent missing')
            boss=caller.f_locals['boss'];label=ev.target or caller.f_locals.get('target','__enemy__');generation=1
            if label!='__enemy__':
                runs=[r for r in boss._runs if any(t.spec.name==label for t in r.targets) or any(a.id==label for a in r.adds)]
                if len(runs)!=1:raise ValueError('Canonical actual target identity is ambiguous')
                generation=runs[0].opens
            packets.append(dict(owner=names.index(ev.caster),time=v['t'],label=label,generation=generation,damage=ev.damage,extra=ev.extra,skill_name=ev.skill_name))
        except (KeyError,AttributeError,ValueError) as error:errors.append(str(error))
    sys.setprofile(profile)
    try:native,trace=grouped(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Mixed coordinate landing observation failed: '+str(errors))
    if not codes:raise ValueError('Canonical real landing function was not observed')
    native['landed_packets']=packets
    return native,trace
