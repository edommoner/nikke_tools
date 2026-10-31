"""Literal direct-boss attack payload shared by all common-world entry packers."""
from portable_world_schedule_specs import number
from portable_enemy_target_specs import target_rule
import copy

DEBUFF_MAGIC=0x42444631

def boss_debuff_effects(patterns, owner):
 """Literal native descriptors; the GPU chooses hit recipients and lifetime."""
 effects=[];nodes={}
 for p in patterns:
  if p.attack is None or not p.attack.debuffs:continue
  start=len(effects);bound=0
  for i,d in enumerate(p.attack.debuffs):
   if d.stat=='dot':raise ValueError('Boss damage-over-time carrier is not connected')
   e=copy.deepcopy(d.effect)
   for key in ('_boss_pattern','_boss_bound'):e.pop(key,None)
   # The legacy compiler needs a squad bucket. The packed definition below
   # replaces it with the native external caster5 before GPU admission.
   e['trigger']={'timing':['battle_start'],'condition':[]}
   effects.append((e,owner))
   if d.duration is None:bound|=1<<i
  if len(effects)-start>32:raise ValueError('Boss attack debuff list exceeds32 definitions')
  nodes[p.idx]=(start,len(effects)-start,bound)
 return effects,nodes

def pack_boss_debuffs(words,metadata,source_start,nodes,L):
 from portable_specs import FIELDS as F
 mapping=metadata['binding_source_indices'];rows=[]
 for node,(start,count,bound) in nodes.items():
  indices=[i for i,source in enumerate(mapping) if source_start+start<=source<source_start+start+count]
  if len(indices)!=count or indices!=list(range(indices[0],indices[0]+count)):
   raise ValueError('Boss debuff compiler bindings must remain one contiguous definition each')
  at=L['WORLD_FRAME_PAYLOAD_BASE']+node*16
  words[at+4:at+8]=[indices[0]+1,count,DEBUFF_MAGIC,bound]
  for row in indices:
   definition=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
   words[definition+F['OWNER']]=5
   words[definition+F['RECIPIENTS']]=0
   extra=L['DEFINITION_EXTRA_BASE']+row*L['DEFINITION_EXTRA_WORDS']
   words[extra]=row;words[extra+2]=0xffffffff
   words[L['RECIPIENT_BASE']+row*8+7]=0
   rows.append(row)
 metadata['boss_debuffs']=dict(definitions=rows,nodes=nodes,external_caster='__enemy__',cpu_recipients_or_schedule_supplied=False)

def pack_attacks(words,patterns,authored,L):
 for p in patterns:
  if p.attack is None:continue
  raw=authored[p.idx]['spec'];at=L['WORLD_FRAME_PAYLOAD_BASE']+p.idx*16
  if raw.get('debuffs') and not any(words[at+4:at+8]):raise ValueError('Attack debuff payload is not connected')
  descriptor=words[at+4:at+8]
  words[at:at+16]=[32,0,0,int(p.attack.pierce),0,0,0,0,*number(p.attack.atk or 114344),*number(p.attack.coeff),*target_rule({k:raw[k] for k in ('target','ignore_taunt') if k in raw})]
  words[at+4:at+8]=descriptor
