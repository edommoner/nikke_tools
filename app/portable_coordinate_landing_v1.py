"""Expected landing layout; actor pool body+127 coordinate targets."""
from pathlib import Path
from portable_coordinate_numeric_v1 import bits
PROFILE='coordinate-landing-v1'
from portable_coordinate_scene_specs import LAYOUT as SCENE
TARGETS=SCENE['CAPACITY'];SHAPES=SCENE['ROWS'];SHAPE_WORDS=16;HEADER=16
assert SHAPES==TARGETS+1
CUTS=TARGETS*(16+24)+16+2
CUT_OFFSET=16+TARGETS*4+4
INPUT=HEADER+SHAPES*SHAPE_WORDS;PREFIX_OUTPUT=CUT_OFFSET+2*CUTS
PREP_OFFSET=PREFIX_OUTPUT;PREP_WORDS=24;OUTPUT=PREP_OFFSET+SHAPES*PREP_WORDS
MAGIC=0x434c5631
LAYOUT=dict(TARGETS=TARGETS,SHAPES=SHAPES,SHAPE_WORDS=SHAPE_WORDS,HEADER=HEADER,CUTS=CUTS,CUT_OFFSET=CUT_OFFSET,INPUT=INPUT,OUTPUT=OUTPUT,PREP_OFFSET=PREP_OFFSET,PREP_WORDS=PREP_WORDS,MAGIC=MAGIC)
CONSTANTS=dict(MIN_K=bits(2.**-16),MAX_K=bits(65536.),MIN_RADIUS=bits(1e-9),MIN_SPAN=bits(1e-15))
def shader_schema():
    out=['// Generated '+PROFILE]
    out += [f'static const uint CL_{k}={v}U;' for k,v in LAYOUT.items()]
    out += [f'static const uint64_t CL_{k}=(uint64_t(0x{v>>32:08x}U)<<32)|uint64_t(0x{v&0xffffffff:08x}U);' for k,v in CONSTANTS.items()]
    return '\n'.join(out)+'\n'
def check_schema(root=None):assert (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_landing_layout.slang').read_text()==shader_schema(),'Landing layout drift'

def arc_reference_schema(root=None):
    # Slang's default by-value arguments materialize whole 1024-arc copies.
    # Specialize only parameter passing, reusing the exact canonical bodies.
    root=Path(root or Path(__file__).resolve().parents[1])
    source=(root/'gpu/coordinate_arc_sets.slang').read_text()
    subtract=source[source.index('[noinline]\nvoid coordinateArcSubtract'):source.rindex('#endif')]
    subtract=subtract.replace('coordinateArcSubtract(CoordinateArcSet a,CoordinateArcSet b,','coordinateLandingSubtract(inout CoordinateArcSet a,inout CoordinateArcSet b,',1)
    scalar=(root/'gpu/coordinate_arc_scalar.slang').read_text()
    measure=scalar[scalar.index('[noinline]\nuint64_t coordinateArcMeasure'):scalar.index('[noinline]\nvoid coordinateArcInsert')]
    measure=measure.replace('coordinateArcMeasure(CoordinateArcSet value)','coordinateLandingMeasure(inout CoordinateArcSet value)',1)
    assert 'coordinateLandingSubtract' in subtract and 'coordinateLandingMeasure' in measure
    return '// Generated canonical bodies with reference parameters; no arithmetic changes.\n'+subtract+measure

def check_arc_references(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);assert (root/'gpu/coordinate_landing_arc_refs.slang').read_text()==arc_reference_schema(root),'Landing arc reference source drift'

def prepared_arc_schema(root=None):
    # Reuse canonical geometry's arc blocks, supplying invariant frame values.
    root=Path(root or Path(__file__).resolve().parents[1]);source=(root/'gpu/coordinate_geometry_v1.slang').read_text()
    circle=source[source.index('[noinline]\nvoid coordinateCircleArcs'):source.index('[noinline]\nvoid coordinateHalfplaneArcs')]
    circle=circle.replace('coordinateCircleArcs(uint64_t cx,uint64_t cy,uint64_t r,','coordinatePreparedCircleArcs(uint64_t cx,uint64_t cy,uint64_t d,uint64_t r,',1)
    assert 'uint64_t d=coordinateHypot(cx,cy),plus=' in circle
    circle=circle.replace('uint64_t d=coordinateHypot(cx,cy),plus=','uint64_t plus=',1)
    start=source.index('        coordinateRectangleArcs(lx,ly,ew,hh,rho,arcs,valid);')
    end=source.index('        for(uint shape=0;shape<2;shape++)',start);rect=source[start:end]
    old='coordinateCircleArcs(cgSub(cx,lx),cgSub(cy,ly),grow,rho,extra,valid);'
    assert rect.count(old)==1;rect=rect.replace(old,'coordinatePreparedCircleArcs(cgSub(cx,lx),cgSub(cy,ly),cornerDistance[corner],grow,rho,extra,valid);')
    start=rect.index('            uint64_t deg=');end=rect.index('            CoordinateArcSet shifted;',start)
    rect=rect[:start]+rect[end:]
    sets=(root/'gpu/coordinate_arc_sets.slang').read_text()
    intersect=sets[sets.index('[noinline]\nvoid coordinateArcIntersect'):sets.index('[noinline]\nvoid coordinateArcSubtract')]
    intersect=intersect.replace('coordinateArcIntersect(CoordinateArcSet a,CoordinateArcSet b,','coordinatePreparedIntersect(inout CoordinateArcSet a,inout CoordinateArcSet b,',1)
    scalar=(root/'gpu/coordinate_arc_scalar.slang').read_text()
    shift=scalar[scalar.index('[noinline]\nvoid coordinateArcShift'):scalar.rindex('#endif')]
    shift=shift.replace('coordinateArcShift(CoordinateArcSet a,','coordinatePreparedShift(inout CoordinateArcSet a,',1)
    rectangle=source[source.index('[noinline]\nvoid coordinateRectangleArcs'):source.index('// All literal fields')]
    rectangle=rectangle.replace('coordinateRectangleArcs(', 'coordinatePreparedRectangleArcs(').replace('coordinateArcIntersect(', 'coordinatePreparedIntersect(').replace('value=next;', 'coordinatePreparedAssign(value,next);')
    rect=rect.replace('coordinateRectangleArcs(', 'coordinatePreparedRectangleArcs(').replace('coordinateArcShift(', 'coordinatePreparedShift(').replace('arcs=shifted;', 'coordinatePreparedAssign(arcs,shifted);')
    assign='void coordinatePreparedAssign(inout CoordinateArcSet destination,inout CoordinateArcSet source){destination.count=source.count;destination.overflow=source.overflow;for(uint i=0;i<source.count;i++){destination.start[i]=source.start[i];destination.end[i]=source.end[i];}}\n'
    return '// Generated canonical arcs with invariant prepared frame values.\n'+assign+intersect+shift+rectangle+circle+''' 
+[noinline]
+void coordinatePreparedShapeArcs(uint kind,uint64_t cx,uint64_t cy,uint64_t lx,uint64_t ly,uint64_t hw,uint64_t hh,uint64_t by,uint64_t d,uint64_t cornerDistance[4],uint64_t rotation,uint64_t radius,uint64_t rho,uint64_t grow,out CoordinateArcSet arcs,out bool valid)
+{
+    valid=true;coordinateArcClear(arcs);
+    if(kind==1){coordinatePreparedCircleArcs(cx,cy,d,f64Add(radius,grow),rho,arcs,valid);return;}
+    uint64_t ew=f64Add(hw,grow),eh=f64Add(hh,grow);
+'''.replace('\n+','\n')+rect+'''
+    valid=valid&&!arcs.overflow;
+}
+'''.replace('\n+','\n')

def check_prepared_arcs(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);assert (root/'gpu/coordinate_prepared_arcs_v1.slang').read_text()==prepared_arc_schema(root),'Prepared geometry source drift'
