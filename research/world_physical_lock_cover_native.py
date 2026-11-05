"""Observe actual cover notifications and immutable before/after membership."""
from world_frame_native import roster_names
from world_physical_locks_native import observe as physical

def observe(case,*,candidate_observer=None):
    names=roster_names(case);events=[];clears=[]
    def notified(bm,event,t,who):
        if event=='event:cover':
            events.append(dict(owner=names.index(who),time=t,charging=bm.state.get('charging',{}).get(who,False)))
    def state(snapshot):
        return dict(revision=snapshot.revision,handles=[[int(h.kind),h.identity,h.generation] for h in snapshot.handles])
    def cleared(event,t,before,after):clears.append(dict(event=event,time=t,before=state(before),after=state(after)))
    from world_coordinate_manual_native import capture
    manual=capture(case)
    # The primary scope excludes the second, transparency-only native run.
    class Primary:
        def __enter__(self):self.observed=manual.__enter__();return self.observed
        def __exit__(self,*args):return manual.__exit__(*args)
    primary=Primary()
    result=physical(case,clear_observer=cleared,notification_observer=notified,primary_observer=primary,candidate_observer=candidate_observer)
    result.update(primary.observed)
    result['cover_notifications']=events;result['clear_events']=clears
    return result,result['skill_trace']
