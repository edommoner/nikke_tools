"""Literal typed named-state queries;never resolve native recipients or lifetimes."""
import struct
from portable_specs import LIMITS as L
MAGIC=0x57533031

def append_queries(words,metadata,queries,duration):
 if len(words)!=L['WORLD_ACTOR_STATE_INPUT_WORDS']:raise ValueError('Actor state wire dimensions')
 if not isinstance(queries,list):raise ValueError('Typed state queries must be a list')
 step=words[2]-1;last=list(words[L['COMMAND_BASE']+step*8:L['COMMAND_BASE']+(step+1)*8]);assert last[0]==40
 # Existing field query indices are already reserved by the shared field packer.
 offset=len(metadata.get('_authored_field_queries',[]))
 if step+len(queries)>=L['COMMANDS'] or offset+len(queries)>L['COMMANDS']:raise ValueError('Typed state query capacity exceeded')
 for index,q in enumerate(queries):
  if not isinstance(q,(list,tuple)) or len(q)!=5:raise ValueError('Expected who/kind/id/generation/name')
  who,kind,identity,generation,name=q
  if any(type(v) is not int for v in q[:4]) or not 0<=who<5 or not 0<=kind<=5 or not 0<=identity<2**28 or not 1<=generation<2**31 or not isinstance(name,str):raise ValueError('Invalid typed state query')
  names=metadata['states']
  if name not in names:names[name]=max(names.values(),default=-1)+1
  if not 0<=names[name]<L['DEFINITIONS']:raise ValueError('State-name capacity exceeded')
  at=L['COMMAND_BASE']+step*8;words[at:at+8]=[41,*struct.unpack('<II',struct.pack('<d',duration)),who,kind,identity,generation,offset+index]
  at=L['WORLD_ACTOR_STATE_INPUT_BASE']+step*2;words[at:at+2]=[names[name],0];step+=1
 words[L['COMMAND_BASE']+step*8:L['COMMAND_BASE']+(step+1)*8]=last;words[2]=step+1;metadata['actor_state_query_indices']=list(range(offset,offset+len(queries)))
