"""Read actual landed packets through the native lifesteal boundary, without queries."""
import sys,types
from calculator import timeline
from calculator.buff_manager import BuffManager
from calculator.boss_pattern import BossScript
from world_frame_native import roster_names
from world_projectile_native import observe as original_observe


def observe(case):
    names=roster_names(case);events=[];errors=[];previous=sys.getprofile();accounting={}
    codes=[c for c in timeline.simulate.__code__.co_consts if isinstance(c,types.CodeType) and c.co_name=='_apply_lifesteal']
    if len(codes)!=1:raise ValueError('Native landing boundary missing or ambiguous')
    notify=BuffManager.notify.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if case.get('observe_parts_accounting') and event=='return' and frame.f_code is BossScript.finish.__code__:
            accounting['interrupt_damage']=[frame.f_locals['self'].interrupt_dealt.get(name,0) for name in names]
        if event!='call':return
        try:
            values=frame.f_locals
            if frame.f_code is codes[0]:
                ev=values['ev']
                if ev.skill_name!='parts-source':return
                events.append(dict(kind='packet',owner=names.index(ev.caster),time=values['t'],damage=ev.damage,part=ev.part,target=ev.target,extra=ev.extra,reach=ev.reach,part_damage=ev.part_damage,interrupt_reach=ev.interrupt_reach,interrupt_damage=ev.interrupt_damage))
            elif frame.f_code is notify and values['event']=='hit_count:parts-source':
                events.append(dict(kind='named-hit',owner=names.index(values['caster']),time=values['t']))
        except (KeyError,ValueError,TypeError,AttributeError) as error:errors.append(type(error).__name__+': '+str(error))
    sys.setprofile(profile)
    try:native,trace=original_observe(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Native parts observation failed: '+str(errors))
    native['parts_skill_events']=events
    if case.get('observe_parts_accounting'):
        if not accounting:raise ValueError('Native finish accounting missing')
        native['parts_skill_accounting']=accounting
    return native,trace
