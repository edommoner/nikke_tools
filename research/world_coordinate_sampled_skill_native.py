"""Passively capture real skill body/target calculations in the sampled stream."""
import sys

def observe(case):
    import engine_worker
    from calculator import timeline
    from world_coordinate_sampled_parent_native import observe as parent
    from world_frame_native import roster_names
    names=roster_names(case);rows=[];errors=[];previous=sys.getprofile();code=timeline.calc_damage.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='return' or frame.f_code is not code:return
        caller=frame.f_back
        if caller is None or caller.f_code.co_name not in ('_handle_damage_eff','_coord_skill_hits'):return
        try:
            values=caller.f_locals;eff=values['eff'];args=frame.f_locals;buffs=args['buffs'];cs=values.get('cs')
            owner=values.get('caster') if cs is None else cs.name
            rows.append(dict(owner=names.index(owner),time=values['t'],name=eff.get('name',''),
                             target=values.get('g').name if caller.f_code.co_name=='_coord_skill_hits' else '',
                             damage=answer['damage'],critical=answer['is_crit'],crit_fraction=answer['crit_frac'],
                             crit_rate=buffs.get('crit_rate',.15),skill_rate=buffs.get('crit_rate_skill',buffs.get('crit_rate',.15)),
                             atk_pct=buffs.get('atk_pct',0),kind=caller.f_code.co_name))
        except (KeyError,AttributeError,TypeError,ValueError) as e:errors.append(str(e))
    sys.setprofile(profile)
    try:
        with creation_indices(case) as indices:n,t=parent(case)
    finally:sys.setprofile(previous)
    trace_view(n['skill_trace'],indices)
    if errors:raise ValueError('Sampled skill observation failed: '+str(errors))
    n['sampled_skill_damage']=rows
    return n,t

from contextlib import contextmanager
@contextmanager
def creation_indices(case):
    """Observe actual HitEvent objects and the native enclosing hit loop."""
    names={e['name']:i for i,e in enumerate(case['effects']) if e.get('type')=='damage'}
    previous=sys.getprofile();events={};rows=[]
    def remember(ev,frame):
        value=frame.f_locals;row=names[value['eff']['name']]
        assert ev.skill_name==value['eff']['name'] and ev.t==value['t']
        events[id(ev)]=(row,int(value['_'])+1,int(value['hit_count']))
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if frame.f_code.co_name=='_coord_skill_hits' and frame.f_back is not None and frame.f_back.f_code.co_name=='_handle_damage_eff':
            parent=frame.f_back
            if event=='call':remember(parent.f_locals['_dot_events'][-1],parent)
            elif event=='return':
                for ev in answer:remember(ev,parent)
        if frame.f_code.co_name!='_land':return
        ev=frame.f_locals.get('ev')
        if ev is None or ev.skill_name not in names:return
        if event=='call' and not (case.get('coordinate_packet_trace') and ev.target):
            value=events.get(id(ev))
            if value is None:
                row=names[ev.skill_name]
                assert case['effects'][row]['stat']=='dealt_fixed_damage','Missing native creation hit index'
                value=(row,1,1)
            row,hit,hits=value
            rows.append(dict(row=row,created=ev.t,landed=frame.f_locals['t'],amount=ev.damage,hit=hit,hits=hits))
        elif event=='return':events.pop(id(ev),None)
    sys.setprofile(profile)
    try:yield rows
    finally:sys.setprofile(previous)

def trace_view(trace,indices):
    """Keep the legacy trace as evidence; bind labels to actual creation IDs."""
    assert len(trace)==len(indices),'Every retained trace packet needs a creation receipt'
    result=[]
    for row,actual in zip(trace,indices,strict=True):
        assert all(row[k]==actual[k] for k in ('row','created','landed','amount')),'Creation/landing identity changed'
        assert 1<=actual['hit']<=actual['hits']<=1024,'Native hit-loop bounds'
        result.append(dict(row,hit=actual['hit'],hits=actual['hits']))
    return result
