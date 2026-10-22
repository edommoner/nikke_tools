"""Read actual native _land arguments and native routing; never replay on GPU."""
import sys
from unittest.mock import patch
from world_actor_pool_native import actor_bindings
from world_frame_native import observe
def inspect(case):
 from calculator.boss_pattern import BossScript
 names={e['name']:i for i,e in enumerate(case['effects']) if e.get('type')=='damage'};records=[];active=[];event_rows={};handler_starts={};original=BossScript.route;previous=sys.getprofile()
 def profile(frame,event,arg):
  if previous is not None:previous(frame,event,arg)
  if case.get('observe_periodic_skills') and frame.f_code.co_name=='_handle_damage_eff':
   eff=frame.f_locals.get('eff',{});row=eff.get('_portable_observer_row');events=frame.f_locals.get('_dot_events',[])
   if row is not None:
    if event=='call':handler_starts[id(frame)]=len(events)
    elif event=='return':
     for item in events[handler_starts.pop(id(frame),len(events)):]:event_rows.setdefault(id(item),row)
   return
  if frame.f_code.co_name!='_land':return
  ev=frame.f_locals.get('ev')
  if ev is None or ev.skill_name not in names:return
  if event=='call':
   row=dict(row=event_rows.get(id(ev),names[ev.skill_name]),created=ev.t,landed=frame.f_locals['t'],amount=ev.damage,share=ev.damage,recipients=[0])
   records.append(row);active.append(row)
  elif event=='return':active.pop();event_rows.pop(id(ev),None)
 def route(boss,ev,*args,**kwargs):
  result=original(boss,ev,*args,**kwargs)
  if ev.skill_name in names and active:
   lookup={b.label:i for i,b in enumerate(actor_bindings(boss))};row=active[-1]
   row['recipients']=[lookup[label] for label,_ in result]
   weights={w for _,w in result};assert len(weights)<=1
   if weights:
    weight=next(iter(weights));row['share']=ev.damage if weight==1 else round(ev.damage*weight)
  return result
 with patch.object(BossScript,'route',route):
  sys.setprofile(profile)
  try:native=observe(case)
  finally:sys.setprofile(previous)
 assert not active
 counts={}
 for row in records:
  effect=case['effects'][row['row']];tail=effect['stat'].split(':')[1:];hits=int(tail[0]) if tail and tail[0].isdigit() else 1
  owner=case['owners'][row['row']]
  if effect['stat']=='bonus_damage' and 'burst_cast' in effect.get('trigger',{}).get('timing',[]) and str(case['combat']['weapons'][owner].get('stage',0))=='3':
   from named_target_specs import resolve_named_attack
   named=resolve_named_attack(effect,owner,list(zip(case['effects'],case['owners'])))
   if named is not None:hits=named.deferred_bonus_hits
  key=(row['row'],row['created']);hit=counts.get(key,0)%hits+1;counts[key]=counts.get(key,0)+1
  row.update(hit=hit,hits=hits)
 native['target_counters'].pop('events');return native,records
