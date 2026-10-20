"""Literal typed registry for the common GPU world frame;no CPU lifecycle input."""
from portable_specs import LIMITS as L
from world_actor_specs import bindings,MAX_ACTORS
MAGIC=0x57413031
NONE=0xffffffff

def compile_registry(patterns):
 count=1+sum(len(p.targets) if p.kind=='parts' else 0 for p in patterns)+sum(p.summon.count if p.summon else 0 for p in patterns)
 if not 1<=count<=MAX_ACTORS:raise ValueError('World actor capacity exceeded')
 if any(p.kind=='interrupt' for p in patterns):raise ValueError('Interrupt actor adapter is not connected')
 if any(p.summon and (p.summon.attack or p.summon.self_destruct) for p in patterns):raise ValueError('Actor attack/HP landing must be connected before source attacks')
 if any(p.until_cleared for p in patterns):raise ValueError('Actor HP-owned cleared state is not connected')
 rows=sorted(bindings(patterns),key=lambda b:(int(b.kind),b.identity));assert len(rows)==count
 if len({(r.kind,r.label) for r in rows})!=count:raise ValueError('Duplicate native actor labels')
 words=[0]*(L['WORLD_ACTOR_INPUT_WORDS']-L['WORLD_ACTOR_INPUT_BASE']);words[:3]=[MAGIC,count,len(patterns)]
 for p in patterns:
  at=8+p.idx*4
  if p.kind=='parts':words[at:at+2]=[1,len(p.targets)]
  elif p.summon:words[at:at+2]=[2,p.summon.count]
 for slot,b in enumerate(rows):
  at=8+32*4+slot*8
  words[at:at+8]=[int(b.kind),b.identity,b.source,b.run if b.run>=0 else NONE,b.slot,int(b.parent.kind) if b.parent else NONE,b.parent.identity if b.parent else NONE,0]
 return words,rows
