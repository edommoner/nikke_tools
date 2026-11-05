"""Read actual native share plans/portions with profiling, without extra queries."""
import sys,types
from contextlib import contextmanager
from calculator.buff_manager import BuffManager
from effect_runtime import CATALOG,shared_body_heal,body_heal
from heal_sharing_compat import plan
from world_frame_native import roster_names
from world_projectile_native import observe as projectile_native


@contextmanager
def capture(case):
    names=roster_names(case);events=[];errors=[];receipts=[];pending={};previous=sys.getprofile()
    assert CATALOG.handlers['healing_share'].heal_plan is plan,'Native sharing provider changed'
    watched=[plan.__code__,shared_body_heal.__code__,body_heal.__code__,BuffManager.notify.__code__]
    codes=dict(zip(map(id,watched),('plan','shared','portion','notify'),strict=True))
    if case.get('observe_lifesteal'):
        from calculator import timeline
        matches=[c for c in timeline.simulate.__code__.co_consts if isinstance(c,types.CodeType) and c.co_name=='_apply_lifesteal']
        if len(matches)!=1:raise ValueError('Native lifesteal closure missing or ambiguous')
        watched.append(matches[0]);codes[id(matches[0])]='lifesteal'
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        kind=codes.get(id(frame.f_code))
        if not kind:return
        try:
            values=frame.f_locals
            if kind=='plan' and event=='return':
                events.append(dict(kind='plan',owner=names.index(values['name']),time=values['t'],weights=[(names.index(n),w) for n,w in answer]))
            elif kind in ('shared','portion') and event in ('call','return'):
                manager=values['manager'];row=dict(kind=kind+'-'+event,owner=names.index(values['name']),time=values['t'],amount=values['amount'])
                if kind=='shared':row['hp']=[manager.state['hp'].get(n,manager.state['base_stats'][n]['hp']) for n in names]
                elif event=='call':pending[id(frame)]=dict(owner=row['owner'],time=row['time'],amount=row['amount'],before=manager.state['hp'][values['name']])
                elif event=='return':
                    row['after']=answer
                    receipt=pending.pop(id(frame))
                    if type(answer) not in (int,float):raise TypeError('Body clamp did not return HP')
                    receipts.append(dict(receipt,after=answer))
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
    try:yield dict(events=events,receipts=receipts)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Native share observation failed: '+str(errors))
    if pending:raise ValueError('Incomplete native healing receipts')

def observe(case):
    with capture(case) as data:native,trace=projectile_native(case)
    native['heal_share_events']=data['events']
    return native,trace
