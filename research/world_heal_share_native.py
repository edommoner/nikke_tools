"""Read actual native share plans/portions with profiling, without extra queries."""
import sys,types
from calculator.buff_manager import BuffManager
from effect_runtime import CATALOG,shared_body_heal,body_heal
from heal_sharing_compat import plan
from world_frame_native import roster_names
from world_projectile_native import observe as projectile_native


def observe(case):
    names=roster_names(case);events=[];errors=[];previous=sys.getprofile()
    assert CATALOG.handlers['healing_share'].heal_plan is plan,'Native sharing provider changed'
    codes={plan.__code__:'plan',shared_body_heal.__code__:'shared',body_heal.__code__:'portion',BuffManager.notify.__code__:'notify'}
    if case.get('observe_lifesteal'):
        from calculator import timeline
        matches=[c for c in timeline.simulate.__code__.co_consts if isinstance(c,types.CodeType) and c.co_name=='_apply_lifesteal']
        if len(matches)!=1:raise ValueError('Native lifesteal closure missing or ambiguous')
        codes[matches[0]]='lifesteal'
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        kind=codes.get(frame.f_code)
        if not kind:return
        try:
            values=frame.f_locals
            if kind=='plan' and event=='return':
                events.append(dict(kind='plan',owner=names.index(values['name']),time=values['t'],weights=[(names.index(n),w) for n,w in answer]))
            elif kind in ('shared','portion') and event in ('call','return'):
                manager=values['manager'];row=dict(kind=kind+'-'+event,owner=names.index(values['name']),time=values['t'],amount=values['amount'])
                if kind=='shared':row['hp']=[manager.state['hp'].get(n,manager.state['base_stats'][n]['hp']) for n in names]
                elif event=='return':row['after']=answer
                events.append(row)
            elif kind=='lifesteal' and event=='call':
                events.append(dict(kind='lifesteal-call',owner=names.index(values['ev'].caster),time=values['t'],damage=values['ev'].damage))
            elif kind=='notify' and event=='call' and (values['event']=='event:heal_received' or values['event'].startswith(('hp_','event:adjacent_hp_'))):
                row=dict(kind='notify',event=values['event'],owner=names.index(values['caster']),time=values['t'])
                if case.get('observe_heal_sources') and values['event']=='event:heal_received':
                    context=values['ctx'] if 'ctx' in values else values['kwargs']
                    row['heal_source']=names.index(context['heal_source'])
                events.append(row)
        except (KeyError,ValueError,TypeError) as error:errors.append(type(error).__name__+': '+str(error))
    sys.setprofile(profile)
    try:native,trace=projectile_native(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Native share observation failed: '+str(errors))
    native['heal_share_events']=events
    return native,trace
