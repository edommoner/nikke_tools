"""Restore HP-conditioned passives using the requested revival HP percentage.

The pinned engine clears hp_pct during revival to suppress transition events,
but then compares that None to numeric thresholds. Keep the transition sentinel
while passives are being restored and supply the requested final percentage to
condition queries. Intermediate max-HP transfers must not emit HP-edge events.
"""
from functools import wraps

def install():
 from calculator.buff_manager import BuffManager
 if getattr(BuffManager.revive,'_nikke_revive_hp_context',False):return
 original_revive=BuffManager.revive;original_reapply=BuffManager._reapply_passives
 original_sync=BuffManager.sync_hp;original_condition=BuffManager._condition_ok;original_runtime=BuffManager._runtime_condition_ok
 missing=object()
 @wraps(original_revive)
 def revive(self,name,t,hp_pct):
  if not self.is_down(name):return original_revive(self,name,t,hp_pct)
  context=getattr(self,'_nikke_revive_percentages',None)
  if context is None:context={};self._nikke_revive_percentages=context
  previous=context.get(name,missing);context[name]=float(hp_pct)
  try:return original_revive(self,name,t,hp_pct)
  finally:
   if previous is missing:context.pop(name,None)
   else:context[name]=previous
 @wraps(original_reapply)
 def reapply(self,name,t):
  if name not in getattr(self,'_nikke_revive_percentages',{}):return original_reapply(self,name,t)
  restoring=getattr(self,'_nikke_revive_restoring',None)
  if restoring is None:restoring={};self._nikke_revive_restoring=restoring
  restoring[name]=restoring.get(name,0)+1
  try:return original_reapply(self,name,t)
  finally:
   restoring[name]-=1
   if not restoring[name]:restoring.pop(name)
 @wraps(original_sync)
 def sync(self,name):
  if getattr(self,'_nikke_revive_restoring',{}).get(name,0):
   self.state['hp_pct'][name]=None;return
  return original_sync(self,name)
 def query(self,fn,args,kwargs):
  percentages=self.state.get('hp_pct',{});replaced=[]
  for name,pct in getattr(self,'_nikke_revive_percentages',{}).items():
   if percentages.get(name) is None:replaced.append(name);percentages[name]=pct
  try:return fn(self,*args,**kwargs)
  finally:
   for name in replaced:percentages[name]=None
 @wraps(original_condition)
 def condition(self,*args,**kwargs):return query(self,original_condition,args,kwargs)
 @wraps(original_runtime)
 def runtime(self,*args,**kwargs):return query(self,original_runtime,args,kwargs)
 revive._nikke_revive_hp_context=True
 BuffManager.revive=revive;BuffManager._reapply_passives=reapply;BuffManager.sync_hp=sync
 BuffManager._condition_ok=condition;BuffManager._runtime_condition_ok=runtime
