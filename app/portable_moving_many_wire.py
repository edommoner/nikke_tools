"""Same literal input and executor; complete maximum-slot frame/segment banks."""
from pathlib import Path
from portable_moving_typed_wire import compile_battle as physical,output_regions as physical_regions,INPUT,MOVEMENT_BASE,MOVEMENT_OUT,LOGICAL_BASE,AIM_WORDS
from portable_enemy_movement_wire import shader_schema as motion_schema,FRAMES,FRAME_WORDS,SEGMENT_WORDS
CAPACITY=262144
SEGMENTS=FRAMES+CAPACITY*FRAME_WORDS
AIM_BASE=MOVEMENT_OUT+SEGMENTS+CAPACITY*SEGMENT_WORDS
OUTPUT=AIM_BASE+AIM_WORDS
SOURCE='gpu/world_moving_many_entry.slang'

def shader_schema():
    return motion_schema(base=MOVEMENT_BASE,out=MOVEMENT_OUT,output=OUTPUT,capacity=CAPACITY)+''.join('static const uint '+k+'='+str(v)+'U;\n' for k,v in dict(TMR_LAG_BASE=LOGICAL_BASE,TMR_AIM_BASE=AIM_BASE,TMR_AIM_WORDS=AIM_WORDS).items())

def check_schema(root=None):
    if (Path(root or Path(__file__).resolve().parents[1])/'gpu/moving_many_layout.slang').read_text()!=shader_schema():raise ValueError('Maximum-slot motion schema drift')

def output_regions():
    from portable_arena_specs import Region
    rows=physical_regions()[:-3]
    rows += [Region('output','movement-frames',MOVEMENT_OUT+FRAMES,CAPACITY*FRAME_WORDS),
        Region('output','movement-segments',MOVEMENT_OUT+SEGMENTS,CAPACITY*SEGMENT_WORDS),
        Region('output','frozen-typed-aim-centers',AIM_BASE,AIM_WORDS)]
    return rows

def compile_battle(prepared,case):
    check_schema();words,meta,actors,scene=physical(prepared,case)
    meta['moving_typed_geometry'].update(output_words=OUTPUT,movement_history_capacity=CAPACITY)
    return words,meta,actors,scene
