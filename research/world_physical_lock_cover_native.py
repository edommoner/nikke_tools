"""Observe actual cover notifications and immutable before/after membership."""
from world_frame_native import roster_names
from world_physical_locks_native import observe as physical

def observe(case):
    names=roster_names(case);events=[];clears=[]
    def notified(bm,event,t,who):
        if event=='event:cover':
            events.append(dict(owner=names.index(who),time=t,charging=bm.state.get('charging',{}).get(who,False)))
    def state(snapshot):
        return dict(revision=snapshot.revision,handles=[[int(h.kind),h.identity,h.generation] for h in snapshot.handles])
    def cleared(event,t,before,after):clears.append(dict(event=event,time=t,before=state(before),after=state(after)))
    result=physical(case,clear_observer=cleared,notification_observer=notified)
    result['cover_notifications']=events;result['clear_events']=clears
    return result,result['skill_trace']
