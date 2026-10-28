"""Literal ADD firing descriptors beside the existing world graph.

The graph remains owned by compile_schedule. Only its unconnected summon
attack field is lowered into this separate bank, never discarded as support.
"""
import copy
import struct
from pathlib import Path
from portable_world_schedule_specs import compile_schedule,INPUT_WORDS as GRAPH_WORDS

MAGIC=0x41445331
BASE=GRAPH_WORDS
HEADER=16
ROWS=32
ROW_WORDS=8
INPUT_WORDS=BASE+HEADER+ROWS*ROW_WORDS
STATE_BASE=65552
QUEUE_BASE=STATE_BASE+128*4
QUEUE_CAP=1024
OUTPUT_WORDS=QUEUE_BASE+QUEUE_CAP*8


def shader_schema():
    constants=dict(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS,BASE=BASE,ROW_BASE=BASE+HEADER,
                   HEAD=65536,STATE=STATE_BASE,QUEUE=QUEUE_BASE,QUEUE_CAP=QUEUE_CAP)
    return '// Generated from portable_add_attack_schedule; declaration addresses only.\n'+''.join(f'static const uint ADS_{name}={value}U;\n' for name,value in constants.items())


def check_schema(root=None):
    if (Path(root or Path(__file__).resolve().parents[1])/'gpu/world_add_attack_layout.slang').read_text()!=shader_schema():raise ValueError('ADD attack schedule declaration schema drift')


def compile_add_schedule(case):
    check_schema()
    from calculator.boss_pattern import validate
    patterns=validate(copy.deepcopy(case['patterns']),squad_size=5)
    original=copy.deepcopy(case);graph_case=copy.deepcopy(case)
    for raw,p in zip(graph_case['patterns'],patterns,strict=True):
        if p.summon is not None and p.summon.attack is not None:
            if p.summon.self_destruct:raise ValueError('Self-destruct ADD launch lifecycle is not connected')
            raw['spec'].pop('attack')
    graph,_=compile_schedule(graph_case)
    words=[0]*(HEADER+ROWS*ROW_WORDS);words[:3]=[MAGIC,1,len(patterns)]
    count=0
    for p in patterns:
        if p.summon is None or p.summon.attack is None:continue
        attack=p.summon.attack
        if attack.hits>0x7fffffff:raise ValueError('ADD shot count exceeds exact integer descriptor range')
        count+=p.summon.count
        at=HEADER+p.idx*ROW_WORDS
        words[at:at+4]=[p.summon.count,attack.hits,*struct.unpack('<II',struct.pack('<d',attack.interval))]
    if not 0<=count<=127:raise ValueError('At most127 attacking ADD slots required')
    words[3]=count
    assert case==original
    return graph+words,patterns
