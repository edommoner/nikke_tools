"""Read actual synchronous force/start/finish reload calls;never resolve targets twice."""
from unittest.mock import patch
from calculator import timeline
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_charge_control_native import observe as charge_native

def observe(case):
 names=roster_names(case);events=[];actors={};start=timeline.CharState._start_reload;finish=timeline.CharState._finish_reload;register=BuffManager.register_instant_handler;initialize=timeline.CharState.__init__
 def initialized(actor,*a,**kw):
  initialize(actor,*a,**kw);actors[actor.name]=actor
 def state(actor,kind,t):
  actors[actor.name]=actor
  return dict(kind=kind,owner=names.index(actor.name),time=t,until=actor.reloading_until,ammo=actor.ammo,phase=actor._charge_phase,full_time=actor._charge_full_t,release_time=actor._hold_release_t)
 def started(actor,t,bm,*a,**kw):
  answer=start(actor,t,bm,*a,**kw);events.append(state(actor,'start',t));return answer
 def finished(actor,t,bm,*a,**kw):
  answer=finish(actor,t,bm,*a,**kw);events.append(state(actor,'finish',t));return answer
 def registered(bm,stat,handler):
  if stat=='force_reload':
   original=handler
   def forced(eff,caster,t,val):
    events.append(dict(kind='force',owner=names.index(caster),name=eff.get('name',''),time=t));return original(eff,caster,t,val)
   handler=forced
  return register(bm,stat,handler)
 with patch.object(timeline.CharState,'__init__',initialized),patch.object(timeline.CharState,'_start_reload',started),patch.object(timeline.CharState,'_finish_reload',finished),patch.object(BuffManager,'register_instant_handler',registered):native,trace=charge_native(case)
 # Every character is captured by the existing charge-control observer. No
 # additional CPU tick, target resolution or arithmetic schedule is performed.
 native['reload_events']=events;native['reload_until']=[actors[n].reloading_until for n in names]
 return native,trace
