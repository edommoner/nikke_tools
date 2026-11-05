"""Declared typed-state model; not pinned native battle or game-rule evidence."""
import array,importlib.util,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_target_cases import fixtures,NONE
from destructible_target_state import DestructibleTargets
from impact_specs import ActorHandle,ActorKind,Impact,HitFamily,HitOutcome
suite=types.SimpleNamespace(INPUT=2048)
s=importlib.util.spec_from_file_location('target_state_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
def words(x):return list(struct.unpack('<II',struct.pack('<d',float(x))))
def bits(x):return struct.pack('<d',float(x)).hex()
def prepare():
 rows=[];cases=fixtures();packed=array.array('I',[len(cases)])
 for c in cases:
  w=[0]*2048;w[:2]=[c['capacity'],len(c['ops'])]
  for i,(op,slot,kind,identity,generation,t,value,other,owner,ownerId,ownerGen,policy) in enumerate(c['ops']):
   at=2+i*32;w[at:at+15]=[op,slot,kind,identity,generation,*words(t),*words(value),*words(other),owner,ownerId,ownerGen,policy]
  rows.append((('reject/' if c['reject'] else '')+c['name'],w,None if c['reject'] else c))
 seed=rows[0][1]
 for name,offset,value in [('zero-capacity',0,0),('capacity129',0,129),('operations33',1,33),('reserved-operand',17,1)]:
  w=list(seed);w[offset]=value;rows.append(('reject/destructible-target-core/'+name,w,None))
 packed=array.array('I',[len(rows)])
 for _,w,_ in rows:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 return rows,packed.tobytes()
def snapshot(world):
 rows=[]
 for slot,r in enumerate(world.rows):
  if r is None:continue
  owner=None if r.owner is None else [int(r.owner.kind),r.owner.identity,r.owner.generation]
  rows.append(dict(slot=slot,handle=[int(r.handle.kind),r.handle.identity,r.handle.generation],owner=owner,alive=r.alive,remaining=bits(r.remaining),capacity=bits(r.capacity),expires=bits(r.expires)))
 return rows
def native_reference(c):
 world=DestructibleTargets(c['capacity']);log=[]
 for op,slot,kind,identity,generation,t,value,other,owner,ownerId,ownerGen,policy in c['ops']:
  world.advance(t);answer=dict(op=op)
  if op==0:world.spawn(slot,ActorHandle(kind,identity,generation),value,other,None if owner==NONE else ActorHandle(owner,ownerId,ownerGen))
  elif op==1:
   result=world.hit(slot,Impact('owner0',ActorHandle(kind,identity,generation),HitFamily.SKILL,HitOutcome(policy),float(value),float(other)));answer.update(result,took=bits(result['took']))
  elif op==2:answer['retired']=world.retire(slot,ActorHandle(kind,identity,generation))
  elif op==3:answer['selected']=list(world.select([ActorKind(i) for i in range(32) if policy&(1<<i)]))
  else:raise ValueError('Unknown target-state operation')
  answer['state']=snapshot(world);log.append(answer)
 return dict(scope='declared_typed_destructible_state_only_not_battle',operations=log)
def decode(block,c):
 assert block[0]==0 and block[1]==len(c['ops']) and block[2]==0,(c['name'],block[:3])
 bit=lambda at:struct.pack('<II',*block[at:at+2]).hex()
 log=[]
 for step,o in enumerate(c['ops']):
  at=2048+step*1824;assert block[at]==o[0] and block[at+1]==0
  answer=dict(op=o[0]);rows=[]
  if o[0]==1:answer.update(delivered=bool(block[at+2]),broken=bool(block[at+3]),took=bit(at+4))
  elif o[0]==2:answer['retired']=bool(block[at+2])
  elif o[0]==3:answer['selected']=[i for i in range(128) if block[at+8+i//32]&(1<<(i%32))]
  for slot in range(c['capacity']):
   p=at+32+slot*14
   if block[p+2]==0:assert not any(block[p:p+14]);continue
   assert block[p+13]==0
   rows.append(dict(slot=slot,handle=list(block[p:p+3]),alive=bool(block[p+3]),remaining=bit(p+4),capacity=bit(p+6),expires=bit(p+8),owner=None if block[p+10]==NONE else list(block[p+10:p+13])))
  answer['state']=rows;log.append(answer)
 # Final arena equals the last complete snapshot, including unused rows.
 if c['ops']:
  last=2048+(len(c['ops'])-1)*1824+32
  assert list(block[16:16+c['capacity']*14])==list(block[last:last+c['capacity']*14])
 return dict(scope='declared_typed_destructible_state_only_not_battle',operations=log)
def compare(block,domain):
 expected=native_reference(domain);actual=decode(block,domain);assert actual==expected,(domain['name'],actual,expected);return expected
def validate_rejection(block,name):assert name.startswith('reject/destructible-target-core/') and block[0]==64 and block[2]==64,(name,block[:3])
