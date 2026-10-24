"""Actual shared weapon groups against complete native CPU battles."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_battle_attack_group_cases import fixtures
from portable_battle_attack_group_input import compile_battle,SOURCE,INPUT_WORDS,OUTPUT_WORDS,HEADER,SLOTS,SLOT_WORDS,LOG,LOG_CAPACITY
from world_battle_attack_group_native import observe
from portable_battle_attack_group_contracts import verify
import engine_worker
spec=importlib.util.spec_from_file_location('attack_group_real_roster',ROOT/'research/verify-world-projectile-rosters.py');real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
spec=importlib.util.spec_from_file_location('attack_group_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
def inspect_native(case):
    n,_=observe(case);verify(case,n);return n
suite.inspect_native=inspect_native

def prepare():
    entries=[]
    for case in fixtures():
        prepared=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,meta=compile_battle(prepared,routing=case['routing'],declared_effects=case.get('declared_effects',[]))
        # Compare original definitions, including the explicitly declared rows.
        import copy
        prepared=copy.deepcopy(prepared)
        for effect in case.get('declared_effects',[]):prepared['effects'].append(dict(effect=copy.deepcopy(effect),owner=case['body']['squad'][0]))
        entries.append((case['name'],words,(case,prepared,words,meta)))
    from portable_specs import LIMITS as L
    seed=entries[0][1];row=next(row for row in range(seed[1]) if seed[L['EVENT_BASE']+row*L['EVENT_WORDS']]==62);at=L['EVENT_BASE']+row*L['EVENT_WORDS']
    mutations=[('magic',[(104400,0)]),('policy',[(104401,0)]),('owners-zero',[(104402,0)]),('owners-unknown',[(104402,32)]),('zero-threshold',[(at+4,0)]),('too-many-targets',[(at+4,129)]),('threshold-mismatch',[(at+4,3)]),('counting-mode',[(at+3,1)]),('payload',[(at+5,1)]),('stage',[(at+7,1)])]
    for label,edits in mutations:
        words=list(seed)
        for offset,value in edits:words[offset]=value
        entries.append(('reject/attack-group-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):return inspect_native(domain[0])
def compare(block,domain):
    case,prepared,words,meta=domain;n=native_reference(domain)
    assert block[0]==0,dict(status=block[0],name=case['name'])
    actual,_,_,differences=real.compare(block,prepared,(words,meta),n['battle'],n['projectile_shots'])
    if differences:raise ValueError(str(dict(difference_count=len(differences),first=differences[:8])))
    assert block[HEADER]==0x41475331 and block[HEADER+3]==block[HEADER+4]==0
    assert block[HEADER+5]==len(n['groups'])<=LOG_CAPACITY
    assert block[HEADER+6]==len(n['notifications'])
    for slot in range(32):assert block[SLOTS+slot*SLOT_WORDS]==0,'Retained group resource leaked'
    import struct
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    for i,(group,shot) in enumerate(zip(n['groups'],n['shots'],strict=True)):
        at=LOG+i*SLOT_WORDS;targets=[[block[at+26+j*4],block[at+27+j*4],block[at+25+j*4]] for j in range(block[at+4])]
        assert block[at]==2 and block[at+1]==case['body']['squad'].index(group['owner'])
        assert block[at+2]==group['identity'] and block[at+3]==group['epoch']
        assert block[at+5]==shot['packets'] and number(at+8)==group['time']
        assert targets==group['targets'],dict(name=case['name'],gpu=targets,cpu=group['targets'])
        notices=[x for x in n['notifications'] if x['key'][1]==group['identity']];assert block[at+10]==len(notices)
    from portable_specs import LIMITS as L
    watched={item['effect']['name'] for item in prepared['effects'] if item['effect'].get('target')=='target' and item['effect'].get('type')=='buff' and any(t.startswith('multi_hit:') for t in item['effect'].get('trigger',{}).get('timing',[]))}
    if watched:
        expected=native_field_bindings(n,watched)
        fields=[]
        for carrier in actual['carriers']:
            if not carrier['active']:continue
            item=prepared['effects'][meta['binding_source_indices'][carrier['definition']]]['effect']
            if item.get('name') not in watched:continue
            base=L['WORLD_ACTOR_RECIPIENT_BASE']+16+carrier['slot']*L['WORLD_ACTOR_RECIPIENT_WORDS']
            for slot in range(words[L['WORLD_ACTOR_INPUT_BASE']+1]):
                if block[base+2+slot//32]&(1<<(slot%32)):
                    binding=L['WORLD_ACTOR_BINDING_BASE']+slot*8
                    fields.append((item['name'],(words[binding],words[binding+1],block[base+8+slot])))
        assert sorted(fields)==expected,dict(name=case['name'],gpu_fields=fields,native_fields=expected)
    # Quantities for every current ADD, not only boss totals or target counts.
    gpu_adds={}
    for slot in range(words[L['WORLD_ACTOR_INPUT_BASE']+1]):
        binding=L['WORLD_ACTOR_BINDING_BASE']+slot*8
        if words[binding]!=5:continue
        state=L['WORLD_ACTOR_POOL_STATE_BASE']+slot*16
        gpu_adds[(5,words[binding+1],block[state])]=(number(state+4),block[state+3])
    expected_adds={tuple(a['handle']):(a['dealt'],a['hits']) for a in n['adds']}
    assert gpu_adds==expected_adds,dict(name=case['name'],gpu_adds=gpu_adds,native_adds=expected_adds)
    names=case['body']['squad']
    assert actual['add_damage']==[n['add_damage'].get(name,0.) for name in names],dict(gpu_add_damage=actual['add_damage'],native_add_damage=n['add_damage'])
    assert number(L['WORLD_ACTOR_POOL_OUTPUT_BASE']+16)==n['add_overkill'],dict(gpu_overkill=number(L['WORLD_ACTOR_POOL_OUTPUT_BASE']+16),native_overkill=n['add_overkill'])
    from portable_battle_attack_group_input import PACKETS
    assert not any(block[PACKETS:PACKETS+L['LANDINGS']]),'Queued group reference bank leaked'
    return n

def native_field_bindings(native,watched):
    # Boss finalization retires add objects after the last battle step. Its
    # object.alive flag is not the recipient binding snapshot used by battle.
    # Use the native carrier's resolved targets and exact current generation.
    current={(0,0,1),*(tuple(a['handle']) for a in native['adds'])}
    return sorted((f['name'],tuple(h)) for f in native['fields'] if f['name'] in watched and f['targets'] for h in f['handles'] if tuple(h) in current)

def validate_rejection(block,name):assert name.startswith('reject/attack-group-') and block[0]==64
