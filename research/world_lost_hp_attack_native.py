"""Observe real buff returns and scalar queries; never issue additional queries."""
import sys
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_parts_skill_native import observe as parts_observe

def observe(case):
    names=roster_names(case);samples=[];values=[];errors=[];previous=sys.getprofile()
    buffs_code=BuffManager.get_buffs.__code__;value_code=BuffManager._get_value.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='return':return
        try:
            if frame.f_code is buffs_code:
                caller=frame.f_back
                if caller is None or caller.f_code.co_name!='_handle_damage_eff' or caller.f_locals.get('eff',{}).get('name') not in ('parts-source','lost-child'):return
                bm=frame.f_locals['self'];caster=frame.f_locals['caster']
                samples.append(dict(owner=names.index(caster),time=caller.f_locals['t'],name=caller.f_locals['eff']['name'],atk_pct=answer['atk_pct'],hp_pct=bm.state['hp_pct'][caster]))
            elif frame.f_code is value_code:
                effect=frame.f_locals['effect']
                if effect.get('scaling')!='lost_hp_pct' or not effect.get('name','').startswith('lost-attack'):return
                carrier=frame.f_locals['carrier'];values.append(dict(owner=names.index(carrier.caster),stack=carrier.stack,value=answer))
        except (KeyError,ValueError,TypeError,AttributeError) as error:errors.append(str(error))
    sys.setprofile(profile)
    try:native,trace=parts_observe(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Lost HP native observation failed: '+str(errors))
    native['lost_hp_attack']=dict(samples=samples,values=values)
    return native,trace
