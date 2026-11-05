"""One full feature-chain kernel owns both coordinate and actual-shot arenas."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_arena_specs import coordinate_layout,attack_group_layout,audit_profile
from portable_coordinate_composed_cases import fixtures
from portable_specs import LIMITS as L
from portable_trigger_specs import pack_event_candidates
from portable_runtime import double_words
from battle_attack_group_runtime import battle_attack_groups
from world_coordinate_skill_native import observe
spec=importlib.util.spec_from_file_location('composed_coordinate_parent',ROOT/'research/verify-coordinate-generation-short.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
spec=importlib.util.spec_from_file_location('composed_coordinate_codec',ROOT/'research/verify-coordinate-skill-short.py')
codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
SOURCE='gpu/world_coordinate_composed_entry.slang';INPUT_WORDS=108648;OUTPUT_WORDS=1310720;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);cross=parent.cross
OLD=coordinate_layout();CP=coordinate_layout(1048576);AG=attack_group_layout()


def composed_words(words,owners=0):
    assert len(words)==108640
    return words[:104400]+[0x41475331,2,owners,1,0,0,0,0]+words[104400:]


def compile_case(case):
    lowered=copy.deepcopy(case)
    for effect in lowered['effects']:
        effect['trigger']['timing']=['event:__portable_attack_group_1' if t=='multi_hit:1' else t for t in effect['trigger']['timing']]
    words,meta,bindings,descriptors=parent.compile_case(lowered)
    for row,source in enumerate(meta['binding_source_indices']):
        timings=case['effects'][source]['trigger']['timing']
        for slot,timing in enumerate(timings):
            if timing!='multi_hit:1':continue
            at=L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8
            assert words[at]==31
            words[at:at+8]=[62,*double_words(1),0,1,0,0,0]
            if slot==0:
                from portable_specs import FIELDS
                words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+FIELDS['EVENT']]=62
    pack_event_candidates(words,L)
    return composed_words(words,1<<case['group_owner']),meta,bindings,descriptors


def prepare():
    assert audit_profile('combined-v1')['address_plan_verified']
    old,_=parent.prepare();entries=[(name,composed_words(words),('retained',domain)) for name,words,domain in old]
    # Rejections keep domain=None so the native oracle remains absent.
    entries=[(name,words,None if domain[1] is None else domain) for name,words,domain in entries]
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case)
        entries.append((case['name'],words,('coexist',(case,meta,bindings,descriptors))))
    seed=entries[88][1]
    for label,offset,value in [('owners',104402,0),('area-old-offset',107592,0),('scene-version',104409,0)]:
        bad=list(seed);bad[offset]=value;entries.append(('reject/coordinate-composed-'+label,bad,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    mode,original=domain
    if mode=='retained':return parent.native_reference(original)
    case=original[0]
    with battle_attack_groups(routing='native') as data:native,trace=observe(case)
    coordinate=native.pop('coordinate_skill');events=native.pop('parts_skill_events')
    for key in ('parts_skill_lifecycle','parts_skill_accounting'):native.pop(key,None)
    handle=lambda h:[int(h.kind),h.identity,h.generation]
    groups=[dict(row,targets=[handle(h) for h in row['targets']]) for row in data['groups']]
    notices=[dict(row,key=[row['key'].caster,row['key'].identity,row['key'].epoch],targets=[handle(h) for h in row['targets']]) for row in data['notifications']]
    assert len(groups)>=3 and len(groups)==len(notices)==len(data['shots'])
    assert all(row['targets']==[[0,0,1]] and row['finished'] for row in groups)
    assert not data['children'] and not data['child_landings']
    assert len(coordinate['selections'])==4 and all(not row['targets'] for row in coordinate['selections'])
    return dict(battle=native,skill_trace=trace,coordinate_selection=coordinate['selections'],coordinate_target_accounting=coordinate['target_accounting'],coordinate_packets=[row for row in events if row['kind']=='packet'],groups=groups,group_shots=data['shots'],group_notices=notices)


def legacy_view(block):
    # Reuse the full old battle/coordinate decoder, relocating only its arena.
    old=array.array('I',block[:1048576]);old[OLD['BASE']:]=block[CP['BASE']:OUTPUT_WORDS]
    return old


def compare(block,domain):
    mode,original=domain;expected=native_reference(domain)
    view=legacy_view(block)
    if mode=='retained':
        # Reuse the current native value rather than rerun the same oracle.
        decoded=codec.compare(view,original,expected=expected)
        assert block[AG['HEADER']+1]==block[AG['HEADER']+6]==block[AG['HEADER']+8]==0
        return decoded
    coordinate={k:v for k,v in expected.items() if not k.startswith('group')}
    codec.compare(view,original,expected=coordinate)
    groups,shots,notices=expected['groups'],expected['group_shots'],expected['group_notices'];head=AG['HEADER']
    assert block[head]==0x41475331 and block[head+1]==len(groups) and block[head+5]==len(groups) and block[head+6]==len(notices)
    assert block[head+3]==block[head+4]==0 and block[head+10]==1
    assert block[head+8]==1<<original[0]['group_owner']
    for slot in range(AG['SLOTS_COUNT']):assert block[AG['SLOTS']+slot*AG['WORDS']]==0
    at=AG['COMPACT']
    for i,(group,shot) in enumerate(zip(groups,shots,strict=True)):
        log=AG['LOG']+i*AG['WORDS'];words=24+4*len(group['targets'])
        assert block[at:at+words]==block[log:log+words]
        assert block[at]==2 and block[at+1]==original[0]['group_owner']
        assert block[at+2]==group['identity'] and block[at+3]==group['epoch']
        assert block[at+4]==len(group['targets']) and block[at+5]==shot['packets']
        assert struct.unpack('<d',struct.pack('<II',*block[at+8:at+10]))[0]==group['time']
        assert block[at+10]==1
        assert [[block[at+26+j*4],block[at+27+j*4],block[at+25+j*4]] for j in range(block[at+4])]==group['targets']
        at+=words
    assert block[head+11]==at-AG['COMPACT']
    assert not any(block[at:1048576])
    return expected


def validate_rejection(block,name):assert name.startswith('reject/') and block[0]==64
