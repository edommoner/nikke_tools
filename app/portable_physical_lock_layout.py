"""Separate lock arena: retain all 32 live actor sets and original output words."""
SOURCE='gpu/world_physical_locks_entry.slang'
INPUT=104400
BASE=786432
PULSE_CAPACITY=63
SHOT_CAPACITY=31
SET_WORDS=520
HEAD=BASE
PULSES=HEAD+16
CANDIDATE=PULSES+PULSE_CAPACITY*16
SNAPSHOTS=CANDIDATE+SET_WORDS
END=SNAPSHOTS+SHOT_CAPACITY*SET_WORDS
OUTPUT=(END+4095)//4096*4096

def shader_layout():
 values=dict(BASE=BASE,HEAD=HEAD,PULSES=PULSES,CANDIDATE=CANDIDATE,SNAPSHOTS=SNAPSHOTS,END=END,OUTPUT=OUTPUT)
 return '// Generated from portable_physical_lock_layout.py; separate from actor sets.\n'+'\n'.join('static const uint PL_'+k+' = '+str(v)+'U;' for k,v in values.items())+'\n'

def check(root):
 from pathlib import Path
 if (Path(root)/'gpu/physical_lock_layout.slang').read_text()!=shader_layout():raise ValueError('Physical lock arena layout differs')
 if CANDIDATE%8 or SNAPSHOTS%8 or END>OUTPUT:raise ValueError('Physical lock arena overlap')
 return dict(input_words=INPUT,output_words=OUTPUT,legacy_prefix_words=BASE,actor_set_capacity=32,lock_snapshot_capacity=SHOT_CAPACITY,pulse_capacity=PULSE_CAPACITY)
