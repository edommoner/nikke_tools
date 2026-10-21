"""Observe native physical returned packets without resolving targets twice."""
from contextlib import contextmanager
from unittest.mock import patch
from calculator import timeline
from world_frame_native import roster_names
from world_reload_native import observe as reload_native

@contextmanager
def capture_projectile_shots(names):
 shots=[];auto=timeline.CharState._fire;charge=timeline.CharState._charge_fire
 def wrapped(original):
  def call(actor,t,*args,**kwargs):
   muzzles=actor.muzzles;mode={'auto':0,'charge':1,'auto_warmup':2}[actor.fire_mode]
   answer=original(actor,t,*args,**kwargs)
   if answer:
    assert len(answer)%muzzles==0 and len({h.damage for h in answer})==1
    shots.append(dict(owner=names.index(actor.name),mode=mode,time=t,pellets=len(answer)//muzzles,muzzles=muzzles,reach=max(h.reach for h in answer),damage=answer[0].damage))
   return answer
  return call
 with patch.object(timeline.CharState,'_fire',wrapped(auto)),patch.object(timeline.CharState,'_charge_fire',wrapped(charge)):yield shots

def observe(case):
 with capture_projectile_shots(roster_names(case)) as shots:native,trace=reload_native(case)
 native['projectile_shots']=shots;return native,trace
