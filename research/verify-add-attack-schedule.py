"""One CUDA/Metal producer and independent original BossScript comparison."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_add_attack_schedule import compile_add_schedule,INPUT_WORDS,OUTPUT_WORDS,BASE,STATE_BASE,QUEUE_BASE,QUEUE_CAP
from portable_add_attack_cases import fixtures
from world_add_attack_native import observe
spec=importlib.util.spec_from_file_location('add_attack_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
SOURCE='gpu/world_add_attack_probe.slang';STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)


def prepare():
    rows=[]
    for case in fixtures():
        words,patterns=compile_add_schedule(case);rows.append((case['name'],words,(case,patterns)))
    seed=rows[0][1]
    for label,at,value in [('magic',BASE,0),('version',BASE+1,2),('node-count',BASE+2,33),('total',BASE+3,128),('reserved',BASE+4,1),('slots',BASE+16,128),('hits',BASE+17,0x80000000),('interval-nan',BASE+19,0x7ff80000),('row-reserved',BASE+20,1),('unused-row',BASE+24,1),('frame-reserved',2067,1)]:
        w=list(seed);w[at]=value;rows.append(('reject/add-attack/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()


def native_reference(domain):return observe(*domain)


def compare(block,domain):
    n=native_reference(domain);case,patterns=domain
    assert len(block)==OUTPUT_WORDS and block[0]==0
    assert block[65536]==0x41445331 and block[65537]==len(n['queued_attacks']) and block[65538]==n['frames']
    assert not any(block[65539:STATE_BASE])
    assert list(block[16:784])==sum(n['states'],[]),'Graph generation, active state, total fired and consumed edges'
    histories=n['history'];assert block[1]==len(histories)
    assert list(block[784:784+len(histories)*4])==sum(histories,[])
    count=block[2];logs=[list(block[2832+i*6:2838+i*6]) for i in range(count)]
    assert [r for r in logs if r[0]!=3]==[r for r in n['log'] if r[0]!=3]
    actual=[list(block[QUEUE_BASE+i*8:QUEUE_BASE+(i+1)*8]) for i in range(block[65537])]
    assert actual==n['queued_attacks'],dict(case=case['name'],actual=actual,expected=n['queued_attacks'])
    assert not any(block[QUEUE_BASE+len(actual)*8:])
    # Cursor state cannot contain a fabricated generation/index or write beyond
    # its own two-word allocation; probe-only death marks own the third word.
    offset=0
    for p in patterns:
        if p.summon is None or p.summon.attack is None:continue
        generation=n['states'][p.idx][1]
        for slot in range(1,p.summon.count+1):
            at=STATE_BASE+offset*4;offset+=1
            shots=[r for r in actual if r[0]==p.idx and r[1]==slot and r[2]==generation]
            assert list(block[at:at+2])==[generation,len(shots)] and block[at+3]==0
    assert not any(block[STATE_BASE+offset*4:QUEUE_BASE])
    return n


def validate_rejection(block,name):assert name.startswith('reject/add-attack/') and block[0]==64 and not any(block[1:])
