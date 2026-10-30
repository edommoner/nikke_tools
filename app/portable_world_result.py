"""Lossless shared world readback projection for product and native verifiers.

Only GPU readbacks and literal pattern identities are decoded. No CPU battle,
health, damage or schedule is used to reconstruct these histories.
"""
import array,struct
from portable_specs import LIMITS as L
from portable_runtime import decode
WF_OUTPUT=L['WORLD_FRAME_OUTPUT_BASE']
WF_TARGETS=L['WORLD_FRAME_TARGET_BASE']
WF_HITS=L['WORLD_FRAME_HIT_BASE']

def read_histories(block,patterns):
 head=WF_OUTPUT
 def num(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 logs=[];query_pattern={};plan=[];down_by_query={}
 for i in range(block[head+2]):
  at=head+2832+i*6;kind,node,arg=block[at:at+3];time=num(at+3)
  if kind==7:
   entry=dict(time=time,pattern=patterns[node]['id'],event='cover_break',outcome='')
   if arg&0x80000000:entry['after_downs']=arg&0x7fffffff
   plan.append(entry);continue
  if kind==6:
   plan.append(dict(revive_after_downs=arg,time=time));continue
  if kind==3:
   if block[at+5]!=0:query=block[at+5]-1
   elif block[0]!=0 and i==block[head+5]-1 and block[head+7]!=0:query=block[head+8]
   else:continue
   query_pattern[query]=patterns[node]['id'];plan.append(query)
  else:plan.append(dict(time=time,pattern=patterns[node]['id'],event={1:'start',2:'end',4:'dispel',5:'destroy'}[kind],outcome={1:'cleared',2:'expired',3:'followed',4:'end'}[arg] if kind==2 else ''))
 hits=[]
 for i in range(block[head+6]):
  at=WF_HITS+i*16;tag,flags=block[at+2:at+4];assert tag&1
  hits.append(dict(time=num(at),pattern=query_pattern[tag>>5],owner=(flags>>3)&7,damage=num(at+4),pierce=bool(flags&1),shield=num(at+6),cover=num(at+8),decoy=num(at+10),hp=num(at+12),hp_after=num(at+14),down=bool(flags&4)))
  if flags&4:down_by_query.setdefault(tag>>5,[]).append(dict(time=num(at),pattern=query_pattern[tag>>5],event='down',outcome=''))
 logs=order_squad_logs(plan,down_by_query)
 return dict(hits=hits,boss_log=logs)

def read_result(block,meta,case):
 ordinary=decode(block[:159744],meta);head=WF_OUTPUT
 world=read_histories(block,case['patterns'])
 q=ordinary['queries'][-1] if ordinary['queries'] else dict(damage=[],allies=ordinary['allies'],covers=ordinary['covers'],combat=dict(weapons=[]))
 return dict(graph_states=[list(block[head+16+i*24:head+16+(i+1)*24]) for i in range(32)],graph_history=[list(block[head+784+i*4:head+784+(i+1)*4]) for i in range(block[head+1])],status=ordinary['status'],damage=q['damage'],allies=[{k:a[k] for k in ('hp','max_hp','hp_pct','defense','down','received_damage','received_hits')} for a in q['allies']],covers=[{k:a[k] for k in ('hp','max_hp','effective_max_hp')} for a in q['covers']],shots=[w['shots'] for w in q['combat']['weapons']],ammo=[w['ammo'] for w in q['combat']['weapons']],hits=world['hits'],boss_log=world['boss_log'],rng=ordinary['enemy_rng'],target_queries=[list(block[WF_TARGETS+i*8:WF_TARGETS+(i+1)*8]) for i in range(block[head+7])],ordinary=ordinary)

def order_squad_logs(plan,down_by_query):
 pending=[];delivered_downs=0;logs=[]
 def drain(limit=None):
  nonlocal delivered_downs
  while pending and (limit is None or delivered_downs<limit):logs.append(pending.pop(0));delivered_downs+=1
 for item in plan:
  if not isinstance(item,dict):pending.extend(down_by_query.get(item,[]));continue
  if 'revive_after_downs' in item or 'after_downs' in item:
   limit=item.get('revive_after_downs',item.get('after_downs'));drain(limit);assert delivered_downs==limit,'Invalid squad log down ordinal'
   if 'revive_after_downs' in item:logs.append(dict(time=item['time'],pattern='',event='revive',outcome=''))
   else:logs.append({k:v for k,v in item.items() if k!='after_downs'})
  else:drain();logs.append(item)
 drain()
 return logs
def read_overlay_result(block,meta,case):
 original=[];patched=array.array('I',block);head=L['WORLD_FRAME_OUTPUT_BASE']
 for i in range(block[head+2]):
  at=head+2832+i*6;kind=block[at]
  if kind in (3,6):continue
  original.append(kind)
  if kind==4:patched[at]=1
 actual=read_result(patched,meta,case);index=0
 for item in actual['boss_log']:
  if item['event'] in ('down','revive'):continue
  kind=original[index];index+=1
  if kind==4:item['event']='dispel'
 assert index==len(original)
 return actual
