"""Literal ADD collider wire bound to the existing world actor registry.

This is input lowering only. No health, generation, shot schedule, hit list or
damage is stored here. The new bank is not admitted by a legacy GPU entry.
"""
import struct
from pathlib import Path
from types import SimpleNamespace

from coordinate_logical_actor_geometry import normalize
from portable_coordinate_matrix_specs import coefficients
from portable_coordinate_scene_specs import bits
from portable_specs import LIMITS as L

MAGIC=0x4c414731
VERSION=1
LAYOUT=dict(BASE=109968,WORDS=5712,HEADER=32,ROWS=127,ROW_WORDS=32,
            ROW_BASE=32,MAP_BASE=4096,MAP_WORDS=128)
FIELDS=('x','y','r','w','h','rot','z')
SCRATCH=dict(PELLET_BASE=1865584,PELLET_WORDS=2048,HEAD_BASE=1867632,HEAD_WORDS=16,
             OUTPUT_WORDS=2032000)

def shader_schema():
    return '// Generated from portable_logical_geometry_wire; input descriptors only.\n'+''.join(
        f'static const uint LAG_{key}={value}U;\n' for key,value in
        dict(MAGIC=MAGIC,VERSION=VERSION,**LAYOUT,**SCRATCH).items())

def history_schema():
    from portable_skill_history import shader_layout
    source=shader_layout();lines=source.splitlines(keepends=True)
    if not lines[-1].startswith('#define WORLD_SKILL_HISTORY_ADMIT(s) '):raise ValueError('History admission schema changed')
    lines[0]='// Generated logical geometry admission; common skill-history addresses.\n'
    lines[-1]='#define WORLD_SKILL_HISTORY_ADMIT(s) (commands[(s).inputBase+109968U]==0x4c414731U && commands[(s).inputBase+109969U]==1U)\n'
    return ''.join(lines)

def check_schema(root=None):
    path=Path(root or Path(__file__).resolve().parents[1])/'gpu/logical_actor_geometry_layout.slang'
    if path.read_text()!=shader_schema():raise ValueError('Logical geometry shader schema drift')
    history=path.parent/'logical_actor_geometry_history.slang'
    if history.read_text()!=history_schema():raise ValueError('Logical geometry history schema drift')

def output_regions():
    from portable_arena_specs import Region
    from portable_skill_history import BASE,END
    if END!=SCRATCH['PELLET_BASE']:raise ValueError('Logical scratch overlaps skill history')
    return [Region('output','complete-coordinate-output',0,1769856),
            Region('output','logical-reserved-prefix',1769856,BASE-1769856),
            Region('output','common-skill-history',BASE,END-BASE),
            Region('output','logical-pellet-amounts',END,SCRATCH['PELLET_WORDS']),
            Region('output','logical-shot-header',SCRATCH['HEAD_BASE'],16),
            Region('output','logical-reserved-suffix',SCRATCH['HEAD_BASE']+16,SCRATCH['OUTPUT_WORDS']-SCRATCH['HEAD_BASE']-16)]

def input_regions():
    from portable_arena_specs import Region
    base=LAYOUT['BASE']
    return [Region('input','complete-coordinate-input',0,base),
            Region('input','logical-collider-header',base,32),
            Region('input','logical-collider-rows',base+32,4064),
            Region('input','logical-slot-map',base+4096,128),
            Region('input','logical-reserved-tail',base+4224,1488)]

def _row(binding,slot,shape):
    co,si=coefficients(SimpleNamespace(rot=shape['rot'],is_circle=shape['r']>0))
    return [slot,int(binding.kind),binding.identity,binding.source,binding.run,binding.slot,
            1 if shape['r']>0 else 2,0]+sum((bits(v) for v in
            (*(shape[k] for k in FIELDS),co,si)),[])+[0]*6

def pack(spec,bindings):
    rows=normalize(spec)
    if not 1<=len(bindings)<=128 or int(bindings[0].kind)!=0:raise ValueError('Complete BODY-first actor registry required')
    if len({b.label for b in bindings})!=len(bindings):raise ValueError('Ambiguous actor labels')
    lookup={b.label:(i,b) for i,b in enumerate(bindings)}
    words=[0]*LAYOUT['WORDS'];words[:4]=[MAGIC,VERSION,len(rows),len(bindings)]
    for index,row in enumerate(rows):
        selected=lookup.get(row['label'])
        if selected is None or int(selected[1].kind)!=5:raise ValueError('Collider must bind a configured ADD')
        slot,binding=selected
        if binding.source!=2 or not 0<=binding.run<32 or not 0<=binding.slot<128:raise ValueError('Invalid ADD source binding')
        at=LAYOUT['ROW_BASE']+index*LAYOUT['ROW_WORDS']
        words[at:at+LAYOUT['ROW_WORDS']]=_row(binding,slot,row['shape'])
        words[LAYOUT['MAP_BASE']+slot]=index+1
    return words

def validate(words,base_words,bindings):
    """Reject malformed raw banks and any mismatch with the packed actor owner.

    Rotation bytes must be the declared common numeric compiler's output; this
    static validation is not a shader/device execution certificate.
    """
    if len(words)!=LAYOUT['WORDS'] or any(type(v) is not int or not 0<=v<=0xffffffff for v in words):raise ValueError('Logical geometry requires uint32 wire')
    if len(base_words)!=LAYOUT['BASE']:raise ValueError('Complete coordinate input required')
    count=words[2]
    if words[:2]!=[MAGIC,VERSION] or not 1<=count<=127 or words[3]!=len(bindings):raise ValueError('Invalid logical geometry header')
    registry_header=L['WORLD_ACTOR_INPUT_BASE']
    from portable_actor_specs import MAGIC as ACTOR_MAGIC
    if base_words[registry_header:registry_header+2]!=[ACTOR_MAGIC,len(bindings)]:raise ValueError('Actor registry header mismatch')
    spec=[];seen=set()
    for index in range(count):
        at=LAYOUT['ROW_BASE']+index*LAYOUT['ROW_WORDS'];slot=words[at]
        if not 0<slot<len(bindings) or slot in seen:raise ValueError('Invalid or duplicate collider slot')
        seen.add(slot);b=bindings[slot]
        if int(b.kind)!=5:raise ValueError('Collider is not an ADD')
        registry=L['WORLD_ACTOR_BINDING_BASE']+slot*8
        expected=[int(b.kind),b.identity,b.source,b.run,b.slot,0xffffffff,0xffffffff,0]
        if base_words[registry:registry+8]!=expected:raise ValueError('Collider registry owner mismatch')
        values=struct.unpack('<7d',struct.pack('<14I',*words[at+8:at+22]))
        spec.append(dict(label=b.label,shape=dict(zip(FIELDS,values))))
    if words!=pack(spec,bindings):raise ValueError('Noncanonical logical geometry bytes or nonzero reserved bank')
    return dict(colliders=count,actors=len(bindings),gpu_admitted=False,health_copied=False,
                lifecycle_copied=False,rotation_policy='coordinate-area-matrix-common-v1')

def compile_logical_geometry(prepared,spec):
    from portable_coordinate_roster_input import compile_coordinate_battle
    check_schema()
    words,meta,bindings,scene=compile_coordinate_battle(prepared)
    bank=pack(spec,bindings);report=validate(bank,words,bindings)
    meta['logical_actor_geometry_wire']=dict(report,model='literal-add-colliders-v1',
        input_words=LAYOUT['BASE']+LAYOUT['WORDS'],gpu_wire_connected=False)
    return words+bank,meta,bindings,scene
