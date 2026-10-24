"""Coordinate all-parts producer/packet/landing versus full native battle."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_scene_specs import compile_scene,LAYOUT as C
from portable_coordinate_packet_specs import LAYOUT as P,check_schema
from portable_coordinate_skill_cases import fixtures as reference_cases
from portable_coordinate_skill_contracts import verify
from world_coordinate_skill_native import observe
from world_frame_native import roster_names
from portable_specs import LIMITS as L,FIELDS as F,FLAGS
spec=importlib.util.spec_from_file_location('coordinate_skill_battle_base',ROOT/'research/verify-world-heal-share-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
SOURCE='gpu/world_coordinate_skill_entry.slang';BASE_INPUT=104400;INPUT_WORDS=BASE_INPUT+C['INPUT'];OUTPUT_WORDS=1048576;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS,inspect_native=lambda case:native_reference((case,)));cross=parent.cross

def fixtures():
    rows=[]
    for original in reference_cases():
        c=copy.deepcopy(original)
        if not c['contract']['marker'] and c['effects'][-1]['stat']!='bonus_damage':continue
        c['coordinate_packet_trace']=True
        c['coordinate_sources']=[e['name'] for e in c['effects'] if e.get('type')=='damage'];rows.append(c)
    from target_counter_cases import marker
    c=copy.deepcopy(next(c for c in rows if c['name']=='coordinate-skill/same-cast-retired-packets'));c['name']='coordinate-skill/threshold-child-refresh-before-death'
    e=marker('coordinate-counter',1,actor=dict(kind='part',identity=0,generation=1),families=['skill']);e['target']='boss';e['trigger']['timing']=['battle_start','event:target_counter_complete:coordinate-counter'];e['max_trigger']=2
    c['effects'].insert(-1,e);c['owners'].insert(-1,0);c['contract']['counter_refresh_witness']=True;rows.append(c)
    return rows

def compile_case(case):
    # Only remove the shape representation from the existing static graph
    # compiler. The literal descriptor and unchanged effects go to the new
    # coordinate executor; no native target list or computed amount is packed.
    lowered=copy.deepcopy(case);lowered['enemy'].pop('coord',None)
    for pattern in lowered['patterns']:
        for target in pattern.get('targets',[]):
            for key in ('x','y','r','w','h','rotation','z'):target.pop(key,None)
            target['reach']=1
    words,meta,bindings=parent.suite.compile_case(lowered);assert len(words)==BASE_INPUT
    scene=dict(name=case['name'],patterns=case['patterns'],commands=[('capture',case['duration'],0,0)])
    side,descriptors=compile_scene(scene);return words+side,meta,bindings,descriptors

def prepare():
    check_schema();entries=[]
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case);entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    seed=entries[0][1];row=BASE_INPUT+C['ROW_BASE'];damage=next(i for i,e in enumerate(entries[0][2][0]['effects']) if e['type']=='damage');damage_row=entries[0][2][1]['binding_source_indices'].index(damage)
    flags=L['DEFINITION_BASE']+damage_row*L['DEFINITION_WORDS']+F['DAMAGE_FLAGS']
    for label,at,value in [('body-slot',row+5,0),('ordinal',row+3,99),('hp',row+21,0),('radius-unconnected',flags,seed[flags]|FLAGS['PIERCE'])]:
        words=list(seed);words[at]=value;entries.append(('reject/coordinate-skill-'+label,words,None))
    case=copy.deepcopy(fixtures()[0]);case['combat']['weapons'][0].update(charge=.05,min_cycle=.05,interval=.05)
    words,_,_,_=compile_case(case);entries.append(('reject/coordinate-skill-physical-unconnected',words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()

def native_reference(domain):
    case=domain[0];n,t=observe(case);verify(case,n)
    if case['contract'].get('counter_refresh_witness'):
        completions=n['target_counters']['completions'];assert [r['reason'] for r in completions]==['threshold','death'] and [r['credit'] for r in completions]==[1,0] and [r['epoch'] for r in completions]==[1,2]
        assert completions[0]['impact']['family']==1 and completions[0]['actor']['kind']==1
    coordinate=n.pop('coordinate_skill');events=n.pop('parts_skill_events')
    for key in ('parts_skill_lifecycle','parts_skill_accounting'):n.pop(key,None)
    # Every extra target packet has its own ordered trace; the original battle
    # trace now retains only the ordinary body packet, rather than aliasing a
    # target label to BODY. No extra damage/receipt is omitted from comparison.
    return dict(battle=n,skill_trace=t,coordinate_selection=coordinate['selections'],coordinate_target_accounting=coordinate['target_accounting'],coordinate_packets=[e for e in events if e['kind']=='packet'])

def compare(block,domain):
    case,meta,bindings,descriptors=domain;expected=native_reference(domain)
    parent.compare_expected(block[:786432],domain[:3],{key:expected[key] for key in ('battle','skill_trace')})
    assert block[P['BASE']]==0x43534b31 and block[P['BASE']+1]==1
    by_name={r['label']:r for r in descriptors['rows']};names=roster_names(case);account=iter(expected['coordinate_target_accounting']);packets=[]
    for e in expected['coordinate_packets']:
        target=e['target'];r=by_name[target] if target else None;row=next(account) if target else None
        packets.append([e['owner'],r['slot'] if r else 0,r['kind'] if r else 0,row['generation'] if row else 1,*struct.unpack('<II',struct.pack('<d',e['time'])),*struct.unpack('<II',struct.pack('<d',float(e['damage']))),int(bool(target)),0,0,0])
    count=block[P['BASE']+2];assert count==len(packets)
    assert list(block[P['TRACE']:P['TRACE']+count*12])==[word for row in packets for word in row],(case['name'],'coordinate packet/accounting order')
    assert not any(block[P['TRACE']+count*12:P['SELECTION']])
    selection=[]
    for s in expected['coordinate_selection']:
        source=next(i for i,e in enumerate(case['effects']) if e['name']==s['effect_name']);definition=meta['binding_source_indices'].index(source)
        selection.extend([definition,s['hit'],len(s['targets']),0])
        for target,gen in zip(s['targets'],s['generations'],strict=True):
            r=by_name[target];selection.extend([r['slot'],r['kind'],r['identity'],gen])
    used=block[P['BASE']+3];assert block[P['BASE']+4]==len(expected['coordinate_selection']) and used==len(selection)
    assert list(block[P['SELECTION']:P['SELECTION']+used])==selection,(case['name'],'frozen coordinate packet keys')
    assert not any(block[P['SELECTION']+used:])
    return expected

def validate_rejection(block,name):assert name.startswith('reject/coordinate-skill-') and block[0]==64
