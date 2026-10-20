"""Observe original BossScript methods on the same authored graph/clear stimuli."""
import copy,hashlib,struct
from calculator.boss_pattern import BossScript
from portable_world_schedule_specs import OUTCOMES

def bits(value):return list(struct.unpack('<II',struct.pack('<d',float(value))))

def observe(case,patterns):
 names={p.id:p.idx for p in patterns};names['start']=32
 log=[];history=[];snapshots=[];frames=0
 class Observer(BossScript):
  def _open(self,run,t,trigger,events):
   super()._open(run,t,trigger,events)
   labels=[n if o is None else f'{n}({o})' for n,o in run.p.after]
   log.append([1,run.p.idx,labels.index(trigger),*bits(t),0])
  def _close(self,run,t,outcome,events):
   super()._close(run,t,outcome,events)
   history.append([run.p.idx,OUTCOMES[outcome],*bits(t)])
   log.append([2,run.p.idx,OUTCOMES[outcome],*bits(t),0])
 enemy={'def':0,'core_px':0,'patterns':copy.deepcopy(case['patterns'])}
 boss=Observer(patterns,enemy,lambda *_:False)
 def states():
  rows=[]
  for run in boss._runs:
   cleared=run.opens>0 and run.p.until_cleared and (all(not a.alive for a in run.adds) if run.p.summon else all(x.destroyed for x in run.targets if x.spec.breakable))
   rows.append([int(run.active),run.opens,*bits(run.start_t),run.fired,0,int(cleared),0,*run.consumed_after,*([0]*(8-len(run.consumed_after))),*run.consumed_until,*([0]*(8-len(run.consumed_until)))])
  return rows+[[0]*24 for _ in range(32-len(rows))]
 def begin(time,mask=0):
  nonlocal frames
  for run in boss._runs:
   if run.active and mask&(1<<run.p.idx):
    for target in run.targets:target.destroyed=True
    for add in run.adds:add.gone='처치'
  if not boss._ends['start']:history.append([32,0,*bits(time)])
  boss.begin_frame(float(time),enemy);frames+=1
  for hit in boss.attacks:log.append([3,names[hit.pattern],hit.index,*bits(time),0])
  boss.attacks.clear()
 mode=case.get('clock','manual');authored=case.get('frames',[]);through=case.get('duration',authored[-1][0] if authored else 0)
 if mode=='manual':
  for time,mask in case.get('frames',[]):begin(time,mask);snapshots.append(states())
 else:
  begin(0.0);t=0.0;frame=0
  while t<=through and frame<=10800:
   begin(t);frame+=1;t=t+1/60 if mode=='accumulated' else frame/60
 if case.get('finish',True):boss.finish(through)
 return dict(states=states(),history=history,log=log,snapshots=snapshots,frames=frames,native_code_sha256={name:hashlib.sha256(getattr(BossScript,name).__code__.co_code).hexdigest() for name in ('begin_frame','_ready','_close_due','_open','_close','finish')})
