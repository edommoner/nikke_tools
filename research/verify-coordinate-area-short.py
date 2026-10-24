"""Whole-battle ordinary shape selection through existing coordinate packets."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_coordinate_area_specs import compile_area,check_schema,LAYOUT as A
from portable_coordinate_scene_specs import LAYOUT as C
from portable_coordinate_area_cases import fixtures
s=importlib.util.spec_from_file_location('coordinate_area_parent',ROOT/'research/verify-coordinate-dot-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
SOURCE='gpu/world_coordinate_area_entry.slang';INPUT_WORDS=A['BASE_INPUT']+A['INPUT'];OUTPUT_WORDS=1048576;STRICT_WIRE_DIMENSIONS=True;cross=parent.cross
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS,inspect_native=lambda case:parent.native_reference((case,)))
native_reference=parent.native_reference;compare=parent.compare

def compile_case(case):
    import copy
    lowered=copy.deepcopy(case)
    if 'focus_aim_layer2' in case:
        policy=case['focus_aim_layer2'];environment=lowered.setdefault('environment',{})
        if 'focus_aim_layer2' in environment and environment['focus_aim_layer2']!=policy:raise ValueError('Conflicting focus aim policies')
        environment['focus_aim_layer2']=policy
    words,meta,bindings,desc=parent.parent.compile_case(lowered)
    from world_frame_native import authored_metadata,roster_names
    metadata=authored_metadata(case);area=compile_area(case,desc,explosion_ranges=[metadata[n].get('spot_explosion_range') for n in roster_names(case)])
    # The IR uses compiled matrix coefficients; the legacy angle field is zero.
    for i,row in enumerate(desc['rows']):
        at=parent.parent.BASE_INPUT+C['ROW_BASE']+i*C['ROW_WORDS']+16;words[at:at+2]=[0,0]
    return words+area,meta,bindings,desc

def prepare():
    check_schema();entries=[]
    for c in fixtures():
        words,meta,bindings,desc=compile_case(c);entries.append((c['name'],words,(c,meta,bindings,desc)))
    seed=entries[0][1];row=parent.parent.BASE_INPUT+C['ROW_BASE'];area=A['BASE_INPUT'];matrix=area+A['HEADER']+8
    for label,at,value in [('body-slot',row+5,0),('ordinal',row+3,99),('hp',row+21,0),('matrix-nan',matrix+3,0x7ff80000),('matrix-norm',matrix+3,0),('reserved',area+A['INPUT']-1,1),('radius-nan',area+9,0x7ff80000)]:
        w=list(seed);w[at]=value;entries.append(('reject/coordinate-area-'+label,w,None))
    c=fixtures()[0];import copy;c=copy.deepcopy(c);c['combat']['weapons'][0].update(charge=.05,min_cycle=.05,interval=.05);w,_,_,_=compile_case(c);entries.append(('reject/coordinate-area-physical',w,None))
    i=next(i for i,e in enumerate(entries) if e[0]=='coordinate-dot/immediate-three-ticks');c,meta,_,_=entries[i][2];source=next(i for i,e in enumerate(c['effects']) if e['type']=='damage');d=meta['binding_source_indices'].index(source);L,F=parent.parent.L,parent.parent.F
    for label,at in [('no-clock',L['DEFINITION_BASE']+d*L['DEFINITION_WORDS']+F['INTERVAL']),('pending',L['DAMAGE_DEFINITION_BASE']+d*L['DAMAGE_DEFINITION_WORDS']+6)]:
        w=list(entries[i][1])
        if label=='no-clock':w[at:at+2]=[0,0]
        else:w[at]=1
        entries.append(('reject/coordinate-area-'+label,w,None))
    packed=array.array('I',[len(entries)])
    for _,w,_ in entries:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    assert len(entries)==52;return entries,packed.tobytes()
def validate_rejection(block,name):assert name.startswith('reject/coordinate-area-') and block[0]==64
