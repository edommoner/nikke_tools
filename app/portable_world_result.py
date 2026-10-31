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

def read_histories(block,patterns,*,attack_sources=None):
 head=WF_OUTPUT
 def num(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 logs=[];query_pattern={};plan=[];down_by_query={}
 for i in range(block[head+2]):
  at=head+2832+i*6;kind,node,arg=block[at:at+3];time=num(at+3)
  if kind==8:
   plan.append(dict(time=time,pattern=patterns[node]['id'],event='down',outcome='',direct_downs_before=arg));continue
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
  dot=bool(tag&0x80000000)
  pattern=patterns[(tag>>5)&31]['id'] if dot else query_pattern[tag>>5]
  hits.append(dict(time=num(at),pattern=pattern,owner=(flags>>3)&7,damage=num(at+4),pierce=bool(flags&1),shield=num(at+6),cover=num(at+8),decoy=num(at+10),hp=num(at+12),hp_after=num(at+14),down=bool(flags&4)))
  if attack_sources is not None:
   hits[-1]['by']='' if dot else attack_sources[tag>>5]
  if flags&4 and not dot:down_by_query.setdefault(tag>>5,[]).append(dict(time=num(at),pattern=pattern,event='down',outcome=''))
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
  if 'direct_downs_before' in item:
   drain(item['direct_downs_before']);assert delivered_downs==item['direct_downs_before'],'Invalid direct down ordinal'
   logs.append({k:v for k,v in item.items() if k!='direct_downs_before'});delivered_downs+=1;continue
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
  if kind in (3,6,8):continue
  original.append(kind)
  if kind==4:patched[at]=1
 actual=read_result(patched,meta,case);index=0
 for item in actual['boss_log']:
  if item['event'] in ('down','revive'):continue
  kind=original[index];index+=1
  if kind==4:item['event']='dispel'
 assert index==len(original)
 return actual


def read_product_control_log(block,metadata,names,duration,*,burst_trace=None):
    """Project GPU operator intervals through the canonical result formatter.

    Labels are constructor metadata. Decisions and times come only from the
    bounded GPU trace; an open interval is closed at the requested battle end,
    exactly as the native result writer closes its remaining intervals.
    """
    import math
    from portable_specs import LIMITS as L
    from portable_runtime import UnsupportedPortable
    from calculator.sim_result import SimLog,ControlLogEntry
    labels=metadata.get('product_control_labels')
    patterns=metadata.get('product_burst_patterns')
    if not patterns and (not labels or not any(labels)):return None
    h=L['WORLD_CONTROL_HEAD_BASE'];base=L['WORLD_CONTROL_TRACE_BASE'];capacity=L['WORLD_CONTROL_TRACE_COUNT']
    def fail():raise UnsupportedPortable('Invalid or missing GPU operator control history')
    if patterns:
        if len(block)<=h+15 or block[h]!=0x57434831 or block[h+15]!=0x50425031 or block[h+14]>block[8]:fail()
        if burst_trace is not None and block[h+14]!=sum(e['event']==5 for e in burst_trace):fail()
    if not labels or not any(labels):return None
    if len(labels)!=5 or len(names)!=5 or len(block)<base+capacity*8:fail()
    if block[h]!=0x57434831 or block[h+13]!=0x50434c31 or block[h+1]>capacity or block[h+2]>5 or block[h+3]>31:fail()
    if any(block[h+k] for k in ((7,9) if patterns else (7,9,14,15))):fail()
    def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    log=SimLog();active={};preempts={};arbs=0;last_close=None;previous=0.
    def close(who,when):
        opened=active.pop(who,None)
        if opened is None:return None
        start,label=opened
        if when<start:fail()
        if when==start:return None
        entry=ControlLogEntry(start,when,names[who],'click',label['mode'],label['producer'])
        log.control_log.append(entry);return entry
    for index in range(block[h+1]):
        at=base+index*8;kind,who=block[at:at+2];when=number(at+2)
        if not math.isfinite(when) or not previous<=when<=duration:fail()
        previous=when
        if kind==0:
            if who>5 or block[at+4]>31 or block[at+5]>5 or any(block[at+6:at+8]):fail()
            arbs+=1
            if block[at+5]:
                name=names[block[at+5]-1];preempts[name]=preempts.get(name,0)+1
        elif kind==1:
            if who>=5 or block[at+5]!=0 or block[at+4] not in metadata['states'].values():fail()
        elif kind in (2,3):
            row=block[at+4]-1
            if who>=5 or row<0 or row>=len(labels[who]) or any(block[at+6:at+8]):fail()
            label=labels[who][row]
            if label['mode'] not in ('tap','hold','hold_until_close'):fail()
            if kind==2:
                if block[at+5]!=0 or who in active:fail()
                start=when
                if last_close is not None:
                    owner,t,prior,entry=last_close
                    if owner==who and t==when and prior==label and entry is not None:
                        log.control_log.remove(entry);start=entry.t0
                active[who]=(start,label);last_close=None
            else:
                if block[at+5]>1 or who not in active or active[who][1]!=label:fail()
                entry=close(who,when)
                last_close=(who,when,label,entry) if block[at+5]==0 else None
        else:fail()
    if arbs!=block[h+8] or sum(preempts.values())!=block[h+6]:fail()
    for who in range(5):
        if block[L['WORLD_CONTROL_STATE_BASE']+who*32+27]!=preempts.get(names[who],0):fail()
        close(who,duration)
    log.control_preempt=preempts
    return log


def read_product_parts(block,metadata,parts,duration):
    """Original authored parts from GPU pools, extra-hit credit and destruction.

    The factory creates one generation. HP and the time of destruction are
    never reconstructed from input values or a CPU battle.
    """
    import math
    from portable_runtime import UnsupportedPortable
    rows=metadata.get('product_parts',[]);nodes=metadata.get('product_world',{}).get('nodes',[])
    def fail():raise UnsupportedPortable('Invalid or incomplete GPU product part history')
    if not rows or [r['name'] for r in rows]!=[p['name'] for p in parts]:fail()
    head=L['WORLD_ACTOR_POOL_OUTPUT_BASE'];state=L['WORLD_ACTOR_POOL_STATE_BASE'];extra=L['COUNTER_LANDING_EXTRA_BASE'];graph=L['WORLD_FRAME_OUTPUT_BASE']
    if len(block)<L['WORLD_ACTOR_POOL_OUTPUT_WORDS'] or block[head]!=0x57485031:fail()
    count=block[head+1]
    if count!=metadata['real_prepared_input']['actor_bindings'] or not 1<=count<=128 or block[graph+2]>2048:fail()
    selected={r['slot']:r for r in rows}
    if len(selected)!=len(rows) or any(not 0<slot<count for slot in selected):fail()
    def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    destroyed={}
    for i in range(block[graph+2]):
        at=graph+2832+i*6;kind,node,arg=block[at:at+3];when=number(at+3)
        if kind not in (1,2,3,4,5,6,7) or node>=len(nodes) or not math.isfinite(when) or not 0<=when<=duration:fail()
        if kind==5 and arg in selected:
            if node!=selected[arg]['node'] or arg in destroyed:fail()
            destroyed[arg]=when
    result=[]
    for row in rows:
        slot=row['slot'];at=state+slot*16;credit=extra+slot*4
        direct=number(at+6);extra_damage=number(credit+2);damage=direct+extra_damage
        if (block[at]!=1 or block[at+1]>1 or block[at+2]>1
                or bool(block[at+2])!=(slot in destroyed)
                or any(not math.isfinite(v) or v<0 for v in (direct,extra_damage,damage))
                or block[at+3]>0x7fffffff or block[credit]>0x7fffffff):fail()
        result.append(dict(name=row['name'],damage=damage,hits=block[at+3]+block[credit],
            destroyed=slot in destroyed,destroyed_at=round(destroyed[slot],6) if slot in destroyed else None))
    return result
