"""Observe native fractional calls and the actual retained accumulator keys."""
import inspect
from contextlib import contextmanager
from unittest.mock import patch
from calculator import timeline
@contextmanager
def observe_fractional(capture,names):
 original=timeline._notify_frac;capture['fractional_hits']=[]
 def observed(manager,key,name,frac,fire):
  if key not in ('crit_hit','core_hit'):return original(manager,key,name,frac,fire)
  when=inspect.currentframe().f_back.f_locals['t'];count=[];row=dict(event=22 if key=='crit_hit' else 23,owner=names.index(name),time=when,fraction=frac);capture['fractional_hits'].append(row)
  def fired():count.append(1);return fire()
  answer=original(manager,key,name,frac,fired);acc=manager.state['rng_acc'];row.update(fired=len(count),created=(key,name) in acc,after=acc.get((key,name),0.0));return answer
 with patch.object(timeline,'_notify_frac',observed):yield

def accumulators(manager,names):
 return [dict(event=22 if key=='crit_hit' else 23,owner=names.index(name),value=value) for (key,name),value in sorted(((k,v) for k,v in manager.state['rng_acc'].items() if k[0] in ('crit_hit','core_hit')),key=lambda item:(names.index(item[0][1]),item[0][0])) if key in ('crit_hit','core_hit')]
