"""Observe actual native team fraction calls and the shared squad counter."""
import inspect
from unittest.mock import patch
from calculator import timeline
from world_frame_native import roster_names
from world_skill_native import inspect as full_native

def observe(case):
 names=roster_names(case);notes=[];managers=[];original=timeline._notify_frac
 def observed(manager,key,name,frac,fire):
  if key not in ('squad_part_hit','squad_body_hit'):return original(manager,key,name,frac,fire)
  if not managers:managers.append(manager)
  frame=inspect.currentframe().f_back
  while 't' not in frame.f_locals:frame=frame.f_back
  when=frame.f_locals['t'];fired=[];r=dict(event=44 if key=='squad_part_hit' else 45,owner=names.index(name),time=when,fraction=frac);notes.append(r)
  def call():fired.append(1);return fire()
  answer=original(manager,key,name,frac,call);acc=manager.state['rng_acc'];r.update(fired=len(fired),created=(key,name) in acc,after=acc.get((key,name),0.0));return answer
 with patch.object(timeline,'_notify_frac',observed):native,trace=full_native(case)
 manager=managers[0];acc=manager.state['rng_acc'];counts=manager._event_counts.get('__squad__',{})
 native['team_hits']=notes;native['team_counts']=[counts.get(k,0) for k in ('squad_part_hit','squad_body_hit')]
 native['team_accumulators']=[dict(event=44+kind,owner=who,value=acc[(key,name)]) for who,name in enumerate(names) for kind,key in enumerate(('squad_part_hit','squad_body_hit')) if (key,name) in acc]
 return native,trace
