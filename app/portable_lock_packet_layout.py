"""All live queue links, immutable shot times and a bounded diagnostic trace."""
from portable_physical_lock_layout import INPUT,OUTPUT,END,SHOT_CAPACITY,check as check_locks
from portable_physical_lock_cover_layout import WORDS as MANUAL_WORDS
from portable_specs import LIMITS as L
SOURCE='gpu/world_lock_packet_entry.slang'
TOKENS=END+MANUAL_WORDS
QUEUE_CAPACITY=2048
SHOT_TIMES=TOKENS+QUEUE_CAPACITY
HEAD=(SHOT_TIMES+SHOT_CAPACITY*2+7)//8*8
TRACE=HEAD+16
TRACE_WORDS=16
TRACE_CAPACITY=(OUTPUT-TRACE)//TRACE_WORDS
MAGIC=0x4c503031

def shader_layout():
    values=dict(TOKENS=TOKENS,QUEUE_CAPACITY=QUEUE_CAPACITY,SHOT_TIMES=SHOT_TIMES,HEAD=HEAD,TRACE=TRACE,TRACE_CAPACITY=TRACE_CAPACITY,MAGIC=MAGIC)
    return '// Generated from portable_lock_packet_layout.py.\n'+'\n'.join('static const uint LP_'+k+' = '+str(v)+'U;' for k,v in values.items())+'\n'

def check(root):
    from pathlib import Path
    old=check_locks(root)
    if L['LANDINGS']!=QUEUE_CAPACITY or TRACE_CAPACITY<1 or TRACE+TRACE_CAPACITY*TRACE_WORDS>OUTPUT:raise ValueError('Lock packet queue/trace layout differs')
    if (Path(root)/'gpu/lock_packet_layout.slang').read_text()!=shader_layout():raise ValueError('Lock packet generated layout differs')
    return dict(**old,manual_words=MANUAL_WORDS,token_base=TOKENS,queue_capacity=QUEUE_CAPACITY,shot_times=SHOT_TIMES,trace_base=TRACE,trace_capacity=TRACE_CAPACITY,extra_wire_words=0)
