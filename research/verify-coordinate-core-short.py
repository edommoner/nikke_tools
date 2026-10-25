"""Real live core graph state through the same coordinate physical executor."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('live_core_accum_parent',ROOT/'research/verify-coordinate-accum-emission-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_core_specs import INPUT_WORDS,OUTPUT_WORDS,INPUT,compile_core,check_schema
from portable_coordinate_scene_specs import compile_scene
from portable_coordinate_area_specs import compile_area
from world_frame_native import authored_metadata,roster_names
from portable_coordinate_core_cases import fixtures
SOURCE='gpu/world_coordinate_core_entry.slang';STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);cross=parent.cross

def compile_case(case,*,allow_summons=False,allow_world_nodes=False):
    metadata=authored_metadata(case)
    for name,weapon in zip(roster_names(case),case['combat']['weapons']):
        wire_type=weapon.get('base_weapon_type','MG' if weapon.get('mode')=='auto_warmup' else 'AR')
        if metadata[name]['weapon_type']!=wire_type:raise ValueError('Coordinate core weapon metadata and static combat type disagree')
    lowered=copy.deepcopy(case);lowered['enemy'].pop('coord',None)
    for pattern in lowered['patterns']:
        if pattern['kind']=='core':pattern.pop('x',None);pattern.pop('y',None)
        for target in pattern.get('targets',[]):
            for key in ('x','y','r','w','h','rotation','z'):target.pop(key,None)
            target['reach']=1
    codec=parent.parent.parent.area.parent.parent
    words,meta,bindings=codec.parent.suite.compile_case(lowered)
    scene=dict(name=case['name'],patterns=case['patterns'],commands=[('capture',case['duration'],0,0)])
    side,descriptors=compile_scene(scene,allow_core=True,allow_summons=allow_summons,allow_world_nodes=allow_world_nodes)
    if allow_summons:
        from portable_coordinate_scene_specs import LAYOUT as scene_layout
        for index,row in enumerate(descriptors['rows']):
            slots=[slot for slot,b in enumerate(bindings) if int(b.kind)==row['kind'] and b.identity==row['identity']]
            if len(slots)!=1:raise ValueError('Mixed scene requires one exact actor binding')
            row['slot']=slots[0];side[scene_layout['ROW_BASE']+index*scene_layout['ROW_WORDS']+5]=slots[0]
    area_case=copy.deepcopy(case)
    if area_case['enemy']['coord'].get('auto_aim') is None:area_case['enemy']['coord']['auto_aim']=[0,0]
    area=compile_area(area_case,descriptors,explosion_ranges=[metadata[n].get('spot_explosion_range') for n in roster_names(case)])
    words=parent.parent.parent.composed.composed_words(words+side+area,0)
    assert len(words)==108648
    return words+compile_core(case,descriptors['patterns']),meta,bindings,descriptors

def prepare():
    check_schema(ROOT);old,_=parent.prepare();entries=[]
    for name,words,domain in old:
        tail=[0]*INPUT
        if domain is not None:
            from calculator.boss_pattern import validate
            tail=compile_core(domain[0],validate(domain[0]['patterns'],coord=True))
        entries.append((name,words+tail,domain))
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case);entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    from portable_coordinate_core_specs import BASE_INPUT,HEADER
    seed=entries[len(old)][1]
    for label,offset,value in [('magic',BASE_INPUT,0),('version',BASE_INPUT+1,2),('nodes',BASE_INPUT+2,33),('auto',BASE_INPUT+3,2),('reserved',BASE_INPUT+4,1),('core-nan',BASE_INPUT+HEADER+4+1,0x7ff80000),('noncore-center',BASE_INPUT+HEADER+1,0x3ff00000),('unused-node',INPUT_WORDS-1,1)]:
        words=list(seed);assert words[offset]!=value;words[offset]=value;entries.append(('reject/coordinate-core/'+label,words,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):return parent.native_reference(domain)
def compare(block,domain):
    if domain[0]['name'].startswith('coordinate-core/'):
        expected=native_reference(domain)
        return parent.parent.compare_expected(block,domain,expected,verify_parent_quantity=any(e.get('stat')=='dealt_fixed_damage' for e in domain[0]['effects']))
    return parent.compare(block,domain)
def validate_rejection(block,name):
    if name.startswith('reject/coordinate-core/'):assert block[0]==64,(name,block[0])
    else:parent.validate_rejection(block,name)
