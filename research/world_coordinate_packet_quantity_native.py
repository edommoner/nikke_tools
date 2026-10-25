"""Passive real landing order and full-charge quantities on common geometry."""
import sys,types
from unittest.mock import patch


def observe(case,*,observer=None):
    import engine_worker
    from calculator import timeline
    from calculator.buff_manager import BuffManager
    from world_frame_native import roster_names
    from world_coordinate_physical_common import observe as common
    names=roster_names(case)
    codes=[c for c in timeline.simulate.__code__.co_consts
           if isinstance(c,types.CodeType) and c.co_name=='_apply_lifesteal']
    if len(codes)!=1:raise ValueError('Canonical landed packet boundary changed')
    previous=sys.getprofile();packets=[];notices=[];errors=[];notify=BuffManager.notify
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='call' or frame.f_code is not codes[0]:return
        try:
            value=frame.f_locals;ev=value['ev'];caller=frame.f_back
            while caller is not None and 'boss' not in caller.f_locals:caller=caller.f_back
            if caller is None:raise ValueError('Canonical boss landing frame missing')
            boss=caller.f_locals['boss'];generation=1
            if ev.target:
                generations=[run.opens for run in boss._runs for target in run.targets if target.spec.name==ev.target]
                if len(generations)!=1:raise ValueError('Ambiguous canonical target generation')
                generation=generations[0]
            packets.append(dict(owner=names.index(ev.caster),time=value['t'],target=ev.target,
                                damage=ev.damage,extra=ev.extra,generation=generation,
                                skill_name=ev.skill_name))
        except (KeyError,AttributeError,TypeError,ValueError) as error:errors.append(str(error))
    def notified(manager,event,t,caster,**kwargs):
        if event=='full_charge_hit':
            row=dict(owner=names.index(caster),time=t,dealt=kwargs.get('dealt'))
            if case.get('sampled_vital'):
                frame=sys._getframe(1)
                while frame is not None and not isinstance(frame.f_locals.get('self'),timeline.CharState):frame=frame.f_back
                if frame is None:raise ValueError('Native full-charge character frame missing')
                row['muzzles']=frame.f_locals['self'].muzzles
            notices.append(row)
        return notify(manager,event,t,caster,**kwargs)
    with patch.object(BuffManager,'notify',notified):
        sys.setprofile(profile)
        try:result=(common if observer is None else observer)(case)
        finally:sys.setprofile(previous)
    if errors:raise ValueError('Packet quantity observation failed: '+str(errors))
    result['landed_packets']=packets;result['full_charge_quantities']=notices
    return result
