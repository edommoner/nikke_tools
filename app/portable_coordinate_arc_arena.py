"""Generate resource-backed views of canonical arc bodies, without new arithmetic."""
from pathlib import Path
import re
import portable_coordinate_landing_v1 as landing

CAPACITY=1024;SLOTS=8;HEADER_WORDS=2;ROW_WORDS=2+CAPACITY*4
WORDS=HEADER_WORDS+SLOTS*ROW_WORDS
LANDING_OUTPUT=landing.OUTPUT+WORDS
ARC_PREFIX=4100;ARC_OUTPUT=ARC_PREFIX+WORDS
GUARD_MAGIC=0x41525631;SENTINEL=0x0123456789abcdef;LAST=0xfedcba9876543210

SETS=('coordinateArcClear','coordinateArcAppend','coordinateArcUnion','coordinateArcIntersect','coordinateArcSubtract')
SCALAR=('coordinateArcCreate','coordinateArcMeasure','coordinateArcInsert','coordinateArcShift')
GEOMETRY=('cgFull','coordinateCircleArcs','coordinateHalfplaneArcs','coordinateRectangleArcs','coordinateGeometryV1')
PREPARED=('coordinatePreparedAssign','coordinatePreparedIntersect','coordinatePreparedShift','coordinatePreparedRectangleArcs','coordinatePreparedCircleArcs','coordinatePreparedShapeArcs')
REFS=('coordinateLandingSubtract','coordinateLandingMeasure')
LANDING=('clArcs','clGeometry','clShapeCuts','coordinateLandingV1')
NAMES={name:'arena_'+name for name in (*SETS,*SCALAR,*GEOMETRY,*PREPARED,*REFS,*LANDING)}
# Distinct views for simultaneously live values. Callers supply outputs; these
# slots are private temporaries, not a per-loop allocator or a capacity cut.
LOCALS={
    'coordinateArcShift':('value',dict(fragment=7)),
    'coordinatePreparedShift':('value',dict(fragment=7)),
    'coordinateRectangleArcs':('value',dict(plane=5,next=6)),
    'coordinatePreparedRectangleArcs':('value',dict(plane=5,next=6)),
    'coordinateGeometryV1':('arcs',dict(extra=3,shifted=4)),
    'coordinatePreparedShapeArcs':('arcs',dict(extra=3,shifted=4)),
    'clShapeCuts':('output',dict(arcs=0)),
    'coordinateLandingV1':('output',dict(arcs=0,covered=1,visible=2)),
}

def layout_schema():
    values=dict(CAPACITY=CAPACITY,SLOTS=SLOTS,HEADER_WORDS=HEADER_WORDS,ROW_WORDS=ROW_WORDS,WORDS=WORDS)
    return '// Generated arc arena layout; full interval capacity retained.\n'+''.join(f'static const uint ARC_ARENA_{k}={v}U;\n' for k,v in values.items())

def function(source,name):
    match=re.search(r'(?:\[noinline\]\s*)?(?:void|bool|uint64_t)\s+'+re.escape(name)+r'\s*\(',source)
    if not match:raise ValueError('Canonical function missing: '+name)
    begin=source.index('{',match.end());depth=1;end=begin+1
    while depth:
        if source[end]=='{':depth+=1
        elif source[end]=='}':depth-=1
        end+=1
    return source[match.start():end]

def transform(source,name,*,scratch_offset="CL_OUTPUT"):
    text=function(source,name);at=text.index('{');head,body=text[:at],text[at:]
    head=re.sub(r'\b(?:(?:inout|out)\s+)?CoordinateArcSet\s+(\w+)',r'inout ArcArenaView \1',head)
    anchor,slots=LOCALS.get(name,('',{}));seen=[]
    def declaration(match):
        names=[v.strip() for v in match.group(1).split(',')]
        if not anchor or any(v not in slots for v in names):raise ValueError('Unreviewed arena lifetime: '+name+'/'+str(names))
        seen.extend(names)
        def value(v):
            slot=slots[v]
            return f'arcArenaView(output,{scratch_offset},{slot}U)' if anchor=='output' else f'arcArenaSibling({anchor},{slot}U)'
        return 'ArcArenaView '+','.join(v+'='+value(v) for v in names)+';'
    body=re.sub(r'\bCoordinateArcSet\s+([^;{}]+);',declaration,body)
    if set(seen)!=set(slots):raise ValueError('Arena lifetime declaration drift: '+name)
    body=body.replace('value=next;','arena_coordinatePreparedAssign(value,next);').replace('arcs=shifted;','arena_coordinatePreparedAssign(arcs,shifted);')
    # Value parameters in the public canonical helpers permit aliases. Private
    # arena helpers instead reject output/input aliases before clearing output.
    if name in ('coordinateArcUnion','coordinateArcIntersect','coordinateArcSubtract','coordinatePreparedIntersect','coordinateLandingSubtract'):
        body=body[:1]+'\n    if(!arcArenaDistinct(a,b,value))return;'+body[1:]
    if name in ('coordinateArcShift','coordinatePreparedShift'):
        body=body[:1]+'\n    if(!arcArenaDistinctOne(a,value))return;'+body[1:]
    text=head+body
    for old,new in NAMES.items():text=re.sub(r'\b'+old+r'\b',new,text)
    if 'CoordinateArcSet' in text:raise ValueError('Private arc array escaped arena lowering')
    return text+'\n'

def schemas(root):
    root=Path(root)
    groups=[('coordinate_arc_sets.slang',SETS),('coordinate_arc_scalar.slang',SCALAR),('coordinate_geometry_v1.slang',GEOMETRY),('coordinate_prepared_arcs_v1.slang',PREPARED),('coordinate_landing_arc_refs.slang',REFS),('coordinate_landing_v1.slang',LANDING)]
    header='// Generated canonical bodies with resource views; arithmetic and iteration order retained.\n'
    sets=header;rest=header;resident=header
    for filename,names in groups:
        source=(root/'gpu'/filename).read_text()
        for name in names:
            converted=transform(source,name)
            if name in SETS:sets+=converted
            else:
                rest+=converted
                resident+=transform(source,name,scratch_offset="CRA_SCRATCH_OFFSET").replace("commands[","results[")
    return {'coordinate_arc_arena_layout.slang':layout_schema(),'coordinate_arc_arena_ops.slang':sets,'coordinate_landing_arena_ops.slang':rest,'coordinate_landing_resident_arena_ops.slang':resident}

def check(root):
    root=Path(root);landing.check_schema(root);landing.check_arc_references(root);landing.check_prepared_arcs(root)
    assert f'COORDINATE_ARC_CAPACITY={CAPACITY};' in (root/'gpu/coordinate_arc_sets.slang').read_text()
    for name,text in schemas(root).items():assert (root/'gpu'/name).read_text()==text,'Arena canonical-body drift: '+name
