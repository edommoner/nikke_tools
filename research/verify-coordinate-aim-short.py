"""Persistent per-owner aims in the same full shared state/event executor."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('aim_matrix_parent',ROOT/'research/verify-coordinate-matrix-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_aim_wire import INPUT_WORDS,OUTPUT_WORDS,LAYOUT as A,pack,check_schema
from portable_coordinate_aim_cases import fixtures
from world_coordinate_aim_native import capture
from portable_coordinate_aim_contracts import verify as verify_contract
from portable_specs import LIMITS as L
SOURCE='gpu/world_coordinate_aim_entry.slang';STRICT_WIRE_DIMENSIONS=True
from types import SimpleNamespace
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);cross=parent.cross

def compile_case(case):
    lowered=copy.deepcopy(case)
    for control in lowered.get('controls',[]):control.pop('aim',None)
    lowered.pop('sequence',None)
    if 'focus_aim_layer2' in case:lowered['environment']['focus_aim_layer2']=case['focus_aim_layer2']
    words,meta,bindings,desc=parent.compile_case(lowered)
    if any(c.get('aim') for c in case.get('controls',[])):
        words[L['WORLD_META_BASE']+4]=0x46414330|int(case.get('focus_aim_layer2',False))
    return words+pack(case,desc,meta),meta,bindings,desc

def prepare():
    check_schema(ROOT);old,_=parent.prepare();entries=[]
    for name,words,domain in old:
        tail=[A['MAGIC'],1]+[0]*(A['INPUT']-2)
        if domain is not None:tail=pack(domain[0],domain[3],domain[1])
        entries.append((name,words+tail,domain))
    for case in fixtures():
        case=copy.deepcopy(case);case['name']='coordinate-core/aim/'+case['name'].split('/')[-1]
        words,meta,bindings,desc=compile_case(case);entries.append((case['name'],words,(case,meta,bindings,desc)))
    at=A['BASE_INPUT'];row=at+A['HEADER'];seed=entries[len(old)][1]
    for label,offset,value in [('magic',at,0),('version',at+1,2),('entries',at+8,9),('target',row,0),('priority',row+1,101),('kind',row+2,2),('reserved',row+12,1),('unused-sequence',at+A['SEQUENCE']+3,1)]:
        w=list(seed);w[offset]=value;entries.append(('reject/coordinate-aim/'+label,w,None))
    case=copy.deepcopy(fixtures()[5]);case['control_mode']='strict';w,*_=compile_case(case);entries.append(('reject/coordinate-aim/strict-conflict',w,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    with capture(domain[0]) as observed:result=parent.native_reference(domain)
    if domain[0]['name'].startswith('coordinate-core/aim/'):verify_contract(domain[0],dict(result,coordinate_aim=observed))
    return dict(result,coordinate_aim=observed,pre_aim_native_sha256=cross.digest(result))

def compare_aim(block,domain,observed):
    # The logical-enemy sentinel denotes the geometric auto point, not an ADD
    # handle. Actual BODY/ADD routing is checked separately by group receipts.
    slots={r['label']:r['slot'] for r in domain[3]['rows']};slots.update({'':0,'core':128,'__enemy__:*':0})
    slots.update(domain[3].get('typed_aim_slots',{}))
    if domain[3].get('typed_aim_add_slot'):slots['__enemy__:*']=domain[3]['typed_aim_add_slot']
    h=A['STATE'];frames=observed['frames'];a=0xcbf29ce484222325;b=0x84222325cbf29ce4;mask=(1<<64)-1
    for f in frames:
        words=[*struct.unpack('<II',struct.pack('<d',f['time'])),f['owner']+1,f['camera_mask'],int(f['full_burst']),int(f['charging']),f['cast_mask']]
        for aim in f['aims']:words.extend([slots[aim['target']],*struct.unpack('<IIII',struct.pack('<dd',*aim['point']))])
        for word in words:
            a=((a^word)*0x100000001b3)&mask;b=(((b<<7)|(b>>57))^(word*0x9e3779b185ebca87))&mask
    assert list(block[h:h+4])==[A['MAGIC'],1,1,len(frames)],'Coordinate aim frame coverage'
    assert list(block[h+4:h+8])==[a&0xffffffff,a>>32,b&0xffffffff,b>>32],'Coordinate aim full frame conformance digests'
    for who,aim in enumerate(frames[-1]['aims']):
        at=h+32+who*8;expected=[slots[aim['target']],*struct.unpack('<IIII',struct.pack('<dd',*aim['point'])),0,0,0]
        assert list(block[at:at+8])==expected,('Final coordinate aim bank',who)
    assert not any(block[h+72:h+A['STATE_WORDS']]),'Unused aim state must remain zero'

def compare(block,domain):
    with capture(domain[0]) as observed:result=parent.compare(block,domain)
    if domain[0]['name'].startswith('coordinate-core/aim/'):verify_contract(domain[0],dict(result,coordinate_aim=observed))
    compare_aim(block,domain,observed)
    return dict(result,coordinate_aim=observed,pre_aim_native_sha256=cross.digest(result))

def validate_rejection(block,name):
    if name.startswith('reject/coordinate-aim/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
