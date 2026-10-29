"""Original movement definitions lower into live named carriers, plus literal motion.

No position history, generation, selected actor set or simulated time is packed.
The dedicated consumer reads the ordinary carrier/actor/frame state at runtime.
"""
import copy,struct
from pathlib import Path
from enemy_movement_model import normalize
from portable_specs import LIMITS as L,FIELDS as F

MAGIC=0x454d4231
BASE=115680;HEADER=16;MAP=16;ROWS=272;ROW_WORDS=12;WORDS=1796;INPUT=BASE+WORDS
OUT=1867648;STATE=16;STATE_WORDS=12;FRAMES=1552;CAPACITY=4096;FRAME_WORDS=16
SEGMENTS=FRAMES+CAPACITY*FRAME_WORDS;SEGMENT_WORDS=16;END=OUT+SEGMENTS+CAPACITY*SEGMENT_WORDS;OUTPUT=2032000
SOURCE='gpu/world_enemy_movement_entry.slang'

def bits(x):return list(struct.unpack('<II',struct.pack('<d',float(x))))
def shader_schema():
    return '// Generated from portable_enemy_movement_wire; literal motion only.\n'+''.join(
        'static const uint EMB_'+k+'='+str(v)+'U;\n' for k,v in dict(MAGIC=MAGIC,BASE=BASE,HEADER=HEADER,MAP=MAP,ROWS=ROWS,ROW_WORDS=ROW_WORDS,
        WORDS=WORDS,INPUT=INPUT,OUT=OUT,STATE=STATE,STATE_WORDS=STATE_WORDS,FRAMES=FRAMES,CAPACITY=CAPACITY,FRAME_WORDS=FRAME_WORDS,
        SEGMENTS=SEGMENTS,SEGMENT_WORDS=SEGMENT_WORDS,END=END,OUTPUT=OUTPUT).items())
def check_schema(root=None):
    if (Path(root or Path(__file__).resolve().parents[1])/'gpu/enemy_movement_layout.slang').read_text()!=shader_schema():raise ValueError('Movement wire schema drift')

def compile_battle(prepared,geometry,spec):
    from portable_logical_geometry_wire import compile_logical_geometry
    rules=normalize(spec);before=copy.deepcopy(prepared);lowered=copy.deepcopy(prepared);tags={}
    for i,row in enumerate(prepared['effects']):
        e=row['effect'];stat=e.get('stat')
        if stat not in ('enemy_movement_disable','force_move'):continue
        duration=5. if stat=='enemy_movement_disable' else 2.
        if (e.get('type')!='buff' or e.get('target')!='enemies_in_range' or e.get('duration')!=duration
            or e.get('max_stack')!=1 or e.get('trigger')!={'timing':['burst_cast'],'condition':[]}
            or set(e)-{'source','type','name','trigger','target','stat','polarity','max_stack','duration'}):
            raise ValueError('Only original plain burst movement duration carriers are connected')
        tags[i]=1 if stat=='enemy_movement_disable' else 2
        lowered['effects'][i]['effect']['stat']=''
    if not tags:raise ValueError('Original movement definitions required')
    prefix,meta,bindings,scene=compile_logical_geometry(lowered,geometry)
    if prepared!=before or len(prefix)!=BASE:raise ValueError('Original input changed during movement lowering')
    slots={b.label:i for i,b in enumerate(bindings)};colliders={r['label']:r for r in geometry}
    if set(colliders)!={r['label'] for r in rules['actors']}:raise ValueError('Exact logical collider/motion ownership required')
    words=[0]*WORDS;words[:6]=[MAGIC,1,len(rules['actors']),len(meta['binding_source_indices']),len(bindings),int(rules['precedence']=='force-before-disable')]
    domains=[]
    for original,kind in tags.items():
        row=meta['binding_source_indices'].index(original);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
        if prefix[at+F['KIND']]!=4 or prefix[at+F['STAT']]!=0:raise ValueError('Movement must lower through the existing named duration carrier')
        prefix[at+F['KIND']]=0
        words[MAP+row]=kind;domains.append(dict(row=row,source_row=original,kind=kind))
    for i,rule in enumerate(rules['actors']):
        slot=slots.get(rule['label'])
        if slot is None or slot==0 or int(bindings[slot].kind)!=5:raise ValueError('Motion requires a configured ADD collider')
        at=ROWS+i*ROW_WORDS;words[at]=slot;words[at+4:at+12]=sum((bits(x) for x in [*rule['velocity'],*rule['force_center']]),[])
        if prefix[109968+32+i*32]!=slot:raise ValueError('Movement order must match logical collider order')
    meta['enemy_movement']=dict(model='declared-add-motion-v1',domains=domains,rules=rules,original_effects_preserved=True,gpu_admitted=False)
    return prefix+words,meta,bindings,scene

def output_regions():
    from portable_arena_specs import Region
    return [Region('output','movement-header',OUT,16),Region('output','movement-state',OUT+STATE,128*STATE_WORDS),
        Region('output','movement-frames',OUT+FRAMES,CAPACITY*FRAME_WORDS),Region('output','movement-segments',OUT+SEGMENTS,CAPACITY*SEGMENT_WORDS)]
