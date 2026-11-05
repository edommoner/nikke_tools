"""Whole original battles plus every moving position/segment; shared GPU suite."""
import array,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('movement_logical_base',ROOT/'research/verify-logical-actor-geometry.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
from portable_enemy_movement_cases import fixtures
from portable_enemy_movement_wire import INPUT,OUTPUT,OUT,STATE,STATE_WORDS,FRAMES,FRAME_WORDS,SEGMENTS,SEGMENT_WORDS,END,CAPACITY,MAGIC,BASE,MAP,ROWS
from world_enemy_movement_full_native import prepare_case,observe
from portable_skill_history import require_capacity
SOURCE='gpu/world_enemy_movement_entry.slang';suite=SimpleNamespace(INPUT=INPUT,OUTPUT=OUTPUT)
STRICT_WIRE_DIMENSIONS=True;cross=base.cross;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def prepare():
    entries=[]
    for case in fixtures():
        words,domain=prepare_case(case);entries.append((case['name'],words,domain))
    seed=entries[0][1]
    for label,at,value in [('magic',0,0),('version',1,2),('count',2,128),('definitions',3,0),('actors',4,0),('precedence',5,2),('reserved',6,1),('body-motion',ROWS,0),('nonfinite-speed',ROWS+5,0x7ff00000),('marker-kind',MAP,3)]:
        words=list(seed);words[BASE+at]=value;entries.append(('reject/enemy-movement/'+label,words,None))
    raw=array.array('I',[len(entries)])
    for _,w,_ in entries:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    n=observe(domain);data=n['enemy_movement'];require_capacity(n)
    assert n['original_input_identity']['chars_config_seed_weapon_verified']
    assert len(data['frames'])<=CAPACITY and sum(len(f['segments']) for f in data['frames'])<=CAPACITY,'No movement history truncation'
    return n

def compare_movement(block,domain,native,*,output_base=OUT,capacity=CAPACITY):
    data=native['enemy_movement'];frames=data['frames'];segments=[(frame,segment) for frame in frames for segment in frame['segments']]
    assert len(frames)<=capacity and len(segments)<=capacity,'No movement history truncation'
    segments_base=FRAMES+capacity*FRAME_WORDS
    expected=[0]*(segments_base+capacity*SEGMENT_WORDS);expected[:3]=[MAGIC,len(frames),len(segments)]
    def number(at,value):expected[at:at+2]=struct.unpack('<II',struct.pack('<d',value))
    slots={b.label:i for i,b in enumerate(domain[2])};cursor=0;final={}
    for i,frame in enumerate(frames):
        slot=slots[frame['label']];gen=frame['actor'][2];alive=int(frame['alive']);at=FRAMES+i*FRAME_WORDS
        expected[at:at+5]=[slot,gen,alive,cursor,len(frame['segments'])];number(at+6,frame['time']);number(at+8,frame['position'][0]);number(at+10,frame['position'][1]);final[slot]=frame
        for segment in frame['segments']:
            out=segments_base+cursor*SEGMENT_WORDS;cursor+=1
            expected[out:out+3]=[slot,gen,int(segment['disabled'])+2*int(segment['forced'])]
            for off,val in ((4,segment['start']),(6,segment['end']),(8,segment['before'][0]),(10,segment['before'][1]),(12,segment['after'][0]),(14,segment['after'][1])):number(out+off,val)
    for slot,frame in final.items():
        at=STATE+slot*STATE_WORDS;expected[at]=frame['actor'][2];expected[at+1]=int(frame['alive']);expected[at+8]=1
        number(at+2,frame['time']);number(at+4,frame['position'][0]);number(at+6,frame['position'][1])
    output_end=output_base+len(expected);actual=list(block[output_base:output_end])
    if actual!=expected:
        i=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
        raise AssertionError(dict(field='movement',word=output_base+i,gpu=actual[i],native=expected[i]))
    clean=list(block);clean[output_base:output_end]=[0]*len(expected);return clean

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:native=native_reference(domain)
    clean=compare_movement(block,domain,native)
    base.compare_observed(clean,domain,native,indices)
    return native

def validate_rejection(block,name):assert name.startswith('reject/enemy-movement/') and block[0]==64,(name,block[0])
