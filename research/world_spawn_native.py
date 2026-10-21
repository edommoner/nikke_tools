"""Observe actual notify calls without replacing native event execution."""
from contextlib import contextmanager
from unittest.mock import patch
from calculator.buff_manager import BuffManager
@contextmanager
def observe_notifications(capture,names):
 original=BuffManager.notify;capture['enemy_spawn_notifications']=[]
 def notify(manager,event,t,caster,**ctx):
  if event=='event:enemy_spawn':capture['enemy_spawn_notifications'].append(dict(owner=names.index(caster),time=t))
  return original(manager,event,t,caster,**ctx)
 with patch.object(BuffManager,'notify',notify):yield
