"""Read real source pools;this module never implements their HP arithmetic."""
import struct
from collections import Counter
from impact_specs import ActorHandle,ActorKind
from world_actor_specs import bindings
from calculator.boss_pattern import BOSS_EVENTS
NONE=0xffffffff

def bits(v):return list(struct.unpack('<II',struct.pack('<d',float(v))))
def actor_bindings(boss):return sorted(bindings([r.p for r in boss._runs]),key=lambda b:(int(b.kind),b.identity))
def pool_rows(boss,body_hits=()):
 rows=[]
 for b in actor_bindings(boss):
  if b.run<0:
   dealt=0.
   for h in body_hits:dealt+=float(h.damage)
   rows.append([1,1,0,len(body_hits),*bits(dealt),*bits(dealt),*bits(0),0,0,0,0,0,0]);continue
  r=boss._runs[b.run]
  if r.opens==0:rows.append([0]*16);continue
  if int(b.kind)==1:
   a=r.targets[b.slot];gen=r.opens;alive=r.active and not a.destroyed;reason=int(a.destroyed);hits=a.hits;dealt=a.dealt;landed=a.landed;born=r.start_t;order=0
  else:
   a=r.adds[b.slot];gen=r.opens;alive=r.active and a.alive;reason={'':0,'처치':1,'퇴장':2,'자폭':3}[a.gone];hits=a.hits;dealt=a.dealt;landed=0.;born=a.spawn_t;order=a.order
  rows.append([gen,int(alive),reason,hits,*bits(dealt),*bits(landed),*bits(born),order,0,0,0,0,0])
 return rows

def query_pool(registry,boss,kind,identity,generation,body_hits=()):
 try:snapshot=registry.exact(ActorHandle(kind,identity,generation))
 except ValueError as e:
  status=3 if 'Stale' in str(e) else 2 if 'not spawned' in str(e) else 1;return [status]+[0]*15
 rows=actor_bindings(boss);slot=next(i for i,b in enumerate(rows) if int(b.kind)==kind and b.identity==identity);r=pool_rows(boss,body_hits)[slot]
 return [0,kind,identity,generation,r[1],r[2],r[3],r[10],*r[4:8],*r[8:10],0,0]

def summary(boss,body_hits=(),notice_counts=None,deaths=0):
 return dict(pools=pool_rows(boss,body_hits),score=boss.score,spawned=boss._add_seq,overkill=boss.add_overkill,notice_counts=list(notice_counts or [0]*4),pending_notices=len(boss._carry),deaths=deaths)
