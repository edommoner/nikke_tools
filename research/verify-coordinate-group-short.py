"""Expanded coordinate packets and full shared groups in one resident battle."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
parent=module('group_control_parent','research/verify-coordinate-control-short.py')
core=module('group_core_compiler','research/verify-coordinate-core-short.py')
physical=module('group_physical_codec','research/verify-coordinate-physical-short.py')
from portable_coordinate_group_cases import fixtures
from portable_coordinate_group_contracts import verify
from portable_coordinate_group_wire import INPUT_WORDS,OUTPUT_WORDS,COMPACT,COMPACT_WORDS,check_schema
from portable_coordinate_aim_wire import pack as pack_aim
from portable_specs import LIMITS as L,FIELDS
from portable_runtime import double_words
from portable_trigger_specs import pack_event_candidates
from world_coordinate_group_native import observe
from world_coordinate_aim_native import capture
from world_frame_native import roster_names
SOURCE='gpu/world_coordinate_group_entry.slang';STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);cross=parent.cross

def compile_case(case):
    lowered=copy.deepcopy(case);lowered['enemy'].pop('coord',None)
    # The core compiler preserves authored coordinates and strips them only for
    # the static world compiler. Lower group trigger names, not battle results.
    lowered=copy.deepcopy(case)
    for control in lowered.get('controls',[]):control.pop('aim',None)
    owners=0
    for effect,owner in zip(lowered['effects'],lowered['owners']):
        if any(t.startswith('multi_hit:') for t in effect['trigger']['timing']):owners|=1<<owner
        effect['trigger']['timing']=['event:__portable_attack_group_1' if t.startswith('multi_hit:') else t for t in effect['trigger']['timing']]
    words,meta,bindings,desc=core.compile_case(lowered,allow_summons=True)
    for row,index in enumerate(meta['binding_source_indices']):
        for slot,t in enumerate(case['effects'][index]['trigger']['timing']):
            if not t.startswith('multi_hit:'):continue
            threshold=int(t.split(':')[1]);at=L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8
            assert words[at]==31;words[at:at+8]=[62,*double_words(threshold),0,threshold,0,0,0]
            if slot==0:words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+FIELDS['EVENT']]=62
    pack_event_candidates(words,L);words[104402]=owners
    return words+pack_aim(case,desc,meta),meta,bindings,desc

def prepare():
    check_schema(ROOT);entries,_=parent.prepare()
    for case in fixtures():
        words,meta,bindings,desc=compile_case(case);entries.append((case['name'],words,(case,meta,bindings,desc)))
    seed=entries[-1][1]
    for label,offset,value in [('owners',104402,0),('threshold',L['EVENT_BASE']+(len(fixtures()[-1]['effects'])-1)*L['EVENT_WORDS']+4,129)]:
        bad=list(seed)
        if label=='threshold':
            candidates=[L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8 for row in range(bad[1]) for slot in range(8) if bad[L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8]==62]
            offset=candidates[0]+4
        bad[offset]=value;entries.append(('reject/coordinate-group/'+label,bad,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    if not domain[0]['name'].startswith('coordinate-group-common/'):return parent.native_reference(domain)
    with capture(domain[0]) as aimed:native,trace=observe(domain[0])
    verify(domain[0],native);native['skill_trace']=trace;native['coordinate_aim']=aimed;return native

def compare(block,domain):
    if not domain[0]['name'].startswith('coordinate-group-common/'):
        result=parent.compare(block[:1310720],domain)
        assert not any(block[COMPACT:]),'Unused relocated history must remain zero'
        return result
    expected=native_reference(domain);case,meta,bindings,desc=domain;cp=physical.CP
    physical.codec.compare_expected(block[:786432],domain[:3],dict(battle=expected['battle'],skill_trace=expected['skill_trace']))
    parent.parent.compare_aim(block,domain,expected['coordinate_aim'])
    head=800000;groups=expected['groups'];shots=expected['group_shots'];notices=expected['group_notices'];names=roster_names(case)
    assert block[head]==0x41475331 and block[head+1]==len(groups) and block[head+5]==min(len(groups),64) and block[head+6]==len(notices)
    assert block[head+3]==block[head+4]==0 and block[head+10]==1
    assert all(block[800032+i*536]==0 for i in range(32))
    at=COMPACT;trace=[];by_name={r['label']:r for r in desc['rows']}
    for i,(g,shot) in enumerate(zip(groups,shots,strict=True)):
        words=24+len(g['targets'])*4;group=list(block[at:at+words]);who=names.index(g['owner'])
        assert group[:7]==[2,who,g['identity'],g['epoch'],len(g['targets']),shot['packets'],1],('group header',case['name'],i,group[:7])
        assert struct.unpack('<d',struct.pack('<II',*group[8:10]))[0]==g['time']
        assert group[10]==sum(n['key'][1]==g['identity'] for n in notices)
        assert [[group[26+j*4],group[27+j*4],group[25+j*4]] for j in range(group[4])]==g['targets']
        if i<64:assert block[820000+i*536:820000+i*536+words]==block[at:at+words]
        at+=words
        receipts=iter(r for r in expected['group_receipts'] if r['identity']==g['identity'])
        for pellet in expected['physical_pellets']:
            if pellet['owner']!=g['owner'] or pellet['time']!=g['time']:continue
            for p in pellet['packets']:
                target=by_name.get(p['target'])
                if target:slot=target['slot'];kind=target['kind'];gen=1
                else:
                    handle=next(receipts)['target'];kind,identity,gen=handle
                    slot=next(i for i,b in enumerate(bindings) if int(b.kind)==kind and b.identity==identity)
                trace.append([who,slot,kind,gen,*double_words(pellet['time']),*double_words(p['damage']),int(p['extra']),0,0,0])
        for child in expected['group_child_landings']:
            if child['group_identity']!=g['identity']:continue
            kind,identity,gen=child['target'];slot=next(i for i,b in enumerate(bindings) if int(b.kind)==kind and b.identity==identity)
            trace.append([who,slot,kind,gen,*double_words(child['time']),*double_words(child['damage']),0,0,0,0])
    assert block[head+11]==at-COMPACT and not any(block[at:]),'Full compact history and unused tail'
    start=cp['TRACE'];end=start+len(trace)*12
    assert block[cp['BASE']+2]==len(trace) and list(block[start:end])==sum(trace,[]),(case['name'],'actual routed coordinate packet trace')
    assert not any(block[end:start+cp['TRACE_COUNT']*12])
    return expected

def validate_rejection(block,name):
    if name.startswith('reject/coordinate-group/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
