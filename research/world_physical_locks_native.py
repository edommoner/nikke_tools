"""Transparent observations of native periodic activation and real shots."""
import copy
from contextlib import nullcontext,contextmanager
from unittest.mock import patch
from calculator import timeline
from calculator.buff_manager import BuffManager
from named_generation_locks import NamedGenerationLocks,MODEL,registry_views
from world_actor_runtime import registry_for
from world_frame_native import roster_names
from world_projectile_native import observe as baseline
from world_effect_target_count_shot_native import state as shot_state
MAGIC=0x474c3031

@contextmanager
def capture(case,*,candidate_observer=None,clear_observer=None,notification_observer=None,primary_observer=None,shot_observer=None,enemy_carrier=False):
 if type(enemy_carrier) is not bool:raise ValueError('Explicit enemy carrier policy required')
 names=roster_names(case);owner=case.get('lock_owner',0);caster=names[owner];bosses=[];models={};pulses=[];shots=[];consumed=[];clears=[]
 init=timeline.BossScript.__init__;activate=BuffManager._activate;charge=timeline.CharState._charge_fire;auto=timeline.CharState._fire;notify=BuffManager.notify;consume=BuffManager.consume_bullet_buffs
 def initialized(boss,*a,**kw):init(boss,*a,**kw);bosses.append(boss)
 def model(bm):
  if id(bm) not in models:models[id(bm)]=NamedGenerationLocks(bm,caster,'록 온',base_count=5,capacity_limit=128,eligible_kinds=(0,1,5),model=MODEL)
  return models[id(bm)],registry_for(bm,bosses[-1])
 def provider(reg):
  from world_actor_pool_native import actor_bindings
  bindings=actor_bindings(bosses[-1]);live=[r for r in registry_views(reg) if r.alive and int(r.handle.kind) in (0,5)]
  def key(r):
   if int(r.handle.kind)!=5:return (int(r.handle.kind),r.handle.identity)
   b=next(b for b in bindings if int(b.kind)==5 and b.identity==r.handle.identity)
   return (5,bosses[-1]._runs[b.run].adds[b.slot].order)
  return [r.handle for r in sorted(live,key=key)]
 def activated(bm,effect,who,t,*a,**kw):
  if effect.get('name')=='록 온' and effect.get('stat')==('lock_on' if enemy_carrier else '') and who==caster:
   m,reg=model(bm);cap=m.capacity(t);choices=provider(reg)
   if candidate_observer is not None:candidate_observer(choices)
   answer=m.core.acquire(registry_views(reg),choices,capacity=cap);h=answer.selected
   pulses.append(dict(time=t,receipt=[cap,len(answer.snapshot.handles),answer.snapshot.revision,int(h.kind) if h else 0xffffffff,h.identity if h else 0,h.generation if h else 0,len(answer.removed),MAGIC]))
   if enemy_carrier:
    if h is None:return
    if len(a)>1 or 'targets' in kw:raise ValueError('Lock carrier already has an explicit target override')
    return activate(bm,effect,who,t,*a,targets=[reg.exact(h).label],**kw)
  return activate(bm,effect,who,t,*a,**kw)
 def fired(original):
  def wrapped(actor,t,bm,*a,**kw):
   if actor.name==caster:
    m,reg=model(bm);snap=m.capture(reg,t).state
    shots.append(dict(time=t,revision=snap.revision,handles=[[int(h.kind),h.identity,h.generation] for h in snap.handles]))
    if shot_observer is not None:shot_observer(bm,t,snap)
   return original(actor,t,bm,*a,**kw)
  return wrapped
 def notified(bm,event,t,who=None,*a,**kw):
  if notification_observer is not None:notification_observer(bm,event,t,who)
  if event in ('on_attack','event:cover') and who==caster:
   reason='normal_attack' if event=='on_attack' else 'taking_cover'
   m,reg=model(bm);before=m.clear(reason);clears.append(t)
   if clear_observer is not None:clear_observer(event,t,before,m.core.snapshot())
  return notify(bm,event,t,who,*a,**kw)
 def used(bm,who,t=0.):
  old=shot_state(bm,who,t);answer=consume(bm,who,t);consumed.append(dict(who=names.index(who),time=t,before=old,after=shot_state(bm,who,t)));return answer
 observed=dict(target_count_shots=consumed,lock_pulses=pulses,lock_shots=shots,lock_clears=clears)
 with patch.object(timeline.BossScript,'__init__',initialized),patch.object(BuffManager,'_activate',activated),patch.object(timeline.CharState,'_charge_fire',fired(charge)),patch.object(timeline.CharState,'_fire',fired(auto)),patch.object(BuffManager,'notify',notified),patch.object(BuffManager,'consume_bullet_buffs',used),(primary_observer if primary_observer is not None else nullcontext()):yield observed

def observe(case,**observers):
 before=copy.deepcopy(case)
 with capture(case,**observers) as observed:native,trace=baseline(case)
 plain,plain_trace=baseline(case)
 if native!=plain or trace!=plain_trace or case!=before:raise AssertionError('Lock observer changed complete battle/trace/input')
 return dict(battle=native,skill_trace=trace,**observed)
