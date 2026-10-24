"""Resident physical packets versus the real common-policy CPU battle."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_coordinate_physical_specs import check_schema, audit_arena, LAYOUT
from portable_coordinate_physical_gpu_cases import fixtures
from portable_coordinate_physical_common_contracts import verify
from world_coordinate_physical_common import observe
from world_frame_native import roster_names
from portable_arena_specs import coordinate_layout

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
area=module('physical_coordinate_area','research/verify-coordinate-area-short.py')
composed=module('physical_coordinate_composed','research/verify-coordinate-composed-short.py')
codec=module('physical_coordinate_world','research/verify-world-heal-share-short.py')
cross=codec.cross
SOURCE='gpu/world_coordinate_physical_entry.slang';INPUT_WORDS=LAYOUT['INPUT_WORDS'];OUTPUT_WORDS=LAYOUT['OUTPUT_WORDS'];STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
CP=coordinate_layout(1048576)

def compile_case(case):
    check_schema(ROOT);audit_arena(ROOT)
    words,meta,bindings,descriptors=area.compile_case(case)
    words=composed.composed_words(words,0)
    # The physical numeric profile consumes authored degrees on the GPU.
    # Ordinary skill-area routing retains its existing matrix IR.
    from portable_coordinate_scene_specs import LAYOUT as scene,bits
    for i,row in enumerate(descriptors['rows']):
        at=104408+scene['ROW_BASE']+i*scene['ROW_WORDS']+16
        words[at:at+2]=bits(row['shape'].rot)
    return words,meta,bindings,descriptors

def prepare():
    entries=[]
    for case in fixtures():
        words,meta,bindings,desc=compile_case(case)
        entries.append((case['name'],words,(case,meta,bindings,desc)))
    seed=entries[0][1]
    for name,at,value in [('groups-enabled',104402,1),('scene-magic',104408,0),
                          ('scene-slot',104408+16+5,0),('shape-nan',104408+16+7,0x7ff80000),
                          ('radius',104408+16+11,0xbff00000),('area-magic',107592,0)]:
        words=list(seed);words[at]=value;entries.append(('reject/coordinate-physical/'+name,words,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    answer=observe(domain[0])
    if domain[0]['name'].startswith('coordinate-physical-reference/'):verify(domain[0],answer)
    return answer

def compare(block,domain):
    case,meta,bindings,descriptors=domain;expected=native_reference(domain)
    codec.compare_expected(block[:786432],domain[:3],dict(battle=expected['battle'],skill_trace=expected['skill_trace']))
    by_name={r['label']:r for r in descriptors['rows']};names=roster_names(case);packets=[]
    for row in expected['physical_pellets']:
        for packet in row['packets']:
            target=by_name.get(packet['target']);slot=target['slot'] if target else 0;kind=target['kind'] if target else 0
            packets.append([names.index(row['owner']),slot,kind,1,*struct.unpack('<II',struct.pack('<d',row['time'])),*struct.unpack('<II',struct.pack('<d',float(packet['damage']))),int(packet['extra']),0,0,0])
    assert block[CP['BASE']]==0x43534b31 and block[CP['BASE']+1]==1
    assert block[CP['BASE']+2]==len(packets),(case['name'],'expanded packet count',block[CP['BASE']+2],len(packets))
    start=CP['TRACE'];end=start+len(packets)*CP['TRACE_WORDS']
    assert list(block[start:end])==sum(packets,[]),(case['name'],'ordered physical packet trace')
    assert not any(block[end:start+CP['TRACE_COUNT']*CP['TRACE_WORDS']]),'Unused packet trace must stay zero'
    return expected

def validate_rejection(block,name):
    assert name.startswith('reject/coordinate-physical/') and block[0]==64
