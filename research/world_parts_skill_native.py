"""Read actual landed packets through the native lifesteal boundary, without queries."""
import sys,types
from calculator import timeline
from calculator.buff_manager import BuffManager
from calculator.boss_pattern import BossScript
from world_frame_native import roster_names
from world_projectile_native import observe as original_observe


def observe(case):
    names=roster_names(case);source_names=frozenset(case.get('coordinate_sources',['parts-source']));events=[];errors=[];previous=sys.getprofile();accounting={};lifecycle=[]
    codes=[c for c in timeline.simulate.__code__.co_consts if isinstance(c,types.CodeType) and c.co_name=='_apply_lifesteal']
    if len(codes)!=1:raise ValueError('Native landing boundary missing or ambiguous')
    notify=BuffManager.notify.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        try:
            values=frame.f_locals
            if (case.get('observe_parts_accounting') or any(p.get('kind')=='interrupt' for p in case.get('patterns',[]))) and event=='return' and frame.f_code is BossScript.finish.__code__:
                accounting['interrupt_damage']=[values['self'].interrupt_dealt.get(name,0) for name in names]
                from world_actor_pool_native import actor_bindings
                boss=values['self'];accounting['extra']=[dict(identity=b.identity,generation=boss._runs[b.run].opens,extra_hits=boss._runs[b.run].targets[b.slot].extra_hits,extra_dealt=boss._runs[b.run].targets[b.slot].extra_dealt) for b in actor_bindings(boss) if int(b.kind)==6 and boss._runs[b.run].opens!=0]
            if case.get('observe_parts_lifecycle'):
                if frame.f_code is BossScript.part_hits.__code__ and event=='return' and values['ev'].skill_name in source_names:
                    lifecycle.append(dict(kind='part-capture',time=values['t'],parts=list(answer)))
                elif frame.f_code in (BossScript._open.__code__,BossScript._close.__code__,BossScript._destroy.__code__):
                    run=values.get('run',values.get('r'))
                    if run.p.kind=='parts' and ((frame.f_code is BossScript._open.__code__ and event=='return') or (frame.f_code is not BossScript._open.__code__ and event=='call')):
                        row=dict(kind='part-open' if frame.f_code is BossScript._open.__code__ else 'part-close' if frame.f_code is BossScript._close.__code__ else 'part-destroy',time=values['t'],pattern=run.p.id,ordinal=run.opens)
                        if row['kind']=='part-destroy':row['part']=values['x'].spec.name
                        if row['kind']=='part-close':row['outcome']=values['outcome']
                        lifecycle.append(row)
                elif frame.f_code is notify and event=='call' and values['event']=='event:heal_received':
                    lifecycle.append(dict(kind='heal-notify',owner=names.index(values['caster']),time=values['t']))
            if event!='call':return
            if frame.f_code is codes[0]:
                ev=values['ev']
                if ev.skill_name not in source_names:return
                row=dict(kind='packet',owner=names.index(ev.caster),time=values['t'],damage=ev.damage,part=ev.part,target=ev.target,extra=ev.extra,reach=ev.reach,part_damage=ev.part_damage,interrupt_reach=ev.interrupt_reach,interrupt_damage=ev.interrupt_damage)
                events.append(row)
                if case.get('observe_parts_lifecycle'):lifecycle.append(row.copy())
            elif frame.f_code is notify and values['event'] in {'hit_count:'+name for name in source_names}:
                row=dict(kind='named-hit',owner=names.index(values['caster']),time=values['t']);events.append(row)
                if case.get('observe_parts_lifecycle'):lifecycle.append(row.copy())
        except (KeyError,ValueError,TypeError,AttributeError) as error:errors.append(type(error).__name__+': '+str(error))
    sys.setprofile(profile)
    try:native,trace=original_observe(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Native parts observation failed: '+str(errors))
    native['parts_skill_events']=events
    if case.get('observe_parts_lifecycle'):native['parts_skill_lifecycle']=lifecycle
    if case.get('observe_parts_accounting') or any(p.get('kind')=='interrupt' for p in case.get('patterns',[])):
        if not accounting:raise ValueError('Native finish accounting missing')
        native['parts_skill_accounting']=accounting
    return native,trace
