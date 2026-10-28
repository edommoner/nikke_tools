"""Shared CUDA/Metal complete battle comparison for declared ADD healing."""
import array
import importlib.util
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('enemy_healing_logical_comparison',ROOT/'research/verify-logical-actor-geometry.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_enemy_healing_cases import fixtures
from portable_enemy_healing_contracts import verify
from portable_enemy_healing_wire import LAYOUT,OUTPUT,INPUT_WORDS
from world_enemy_healing_full_native import prepare_case,observe
from portable_skill_history import require_capacity
from portable_specs import LIMITS as L

SOURCE='gpu/world_enemy_healing_entry.slang'
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT['OUTPUT_WORDS'])
cross=base.cross
STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT


def prepare():
    rows=[]
    for case in fixtures():
        words,domain=prepare_case(case);rows.append((case['name'],words,domain))
    seed=rows[0][1]
    for name,offset,value in [('magic',0,0),('version',1,2),('count',2,33),
                              ('reserved',5,1),('source-node',16,0),
                              ('body-target',20,0),('duplicate-target',21,seed[LAYOUT['BASE']+20]),
                              ('nonfinite-amount',19,0x7ff00000)]:
        words=list(seed);words[LAYOUT['BASE']+offset]=value
        rows.append(('reject/enemy-healing/'+name,words,None))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()


def verify_native(domain,native):
    identity=native['original_input_identity']
    assert identity['definitions']==69 and identity['chars_config_seed_weapon_verified']
    data=native['enemy_healing'];public=data['public_summary']
    view=dict(original_input_identity=dict(definitions=identity['definitions'],
              effects_owners_weapons_chars_config_seed_verified=identity['chars_config_seed_weapon_verified'],added_effects=0),
              enemy_healing=data,battle=public)
    verify(dict(contract=domain[0]['enemy_healing_contract']),view)
    require_capacity(native)


def native_reference(domain):
    native=observe(domain);verify_native(domain,native);return native


def compare_healing(block,domain,native):
    case=domain[0];data=native['enemy_healing'];head=OUTPUT['OUTPUT_BASE']
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    assert list(block[head:head+3])==[0x45484C31,len(data['receipts']),len(data['sources'])]
    assert not any(block[head+3:head+16])
    nodes={p['id']:i for i,p in enumerate(case['patterns'])}
    expected_seen=[0]*32
    for source in data['sources']:expected_seen[nodes[source['node']]]=source['generation']
    assert list(block[head+16:head+48])==expected_seen
    slots={b.label:i for i,b in enumerate(domain[2])}
    for index,row in enumerate(data['receipts']):
        at=head+OUTPUT['RECEIPT_BASE']+index*OUTPUT['RECEIPT_WORDS'];status={'not-spawned':1,'dead-or-inactive':2,'healed':3}[row['status']]
        assert list(block[at:at+5])==[nodes[row['node']],row['source_generation'],slots[row['target']],row['actor'][2] if row['actor'] else 0,status]
        assert block[at+5]==0 and number(at+6)==row['time'] and number(at+8)==row['base_amount']
        if status!=3:
            assert not any(block[at+10:at+32]);continue
        for offset,key in [(10,'multiplier'),(12,'requested'),(14,'dealt_before'),(16,'dealt_after'),(18,'applied'),(20,'effective_gain'),(22,'max_hp')]:
            assert number(at+offset)==row[key],dict(case=case['name'],receipt=index,field=key,gpu=number(at+offset),native=row[key])
        assert block[at+24]==row['hits_before'] and block[at+25]==row['hits_after']
        assert not any(block[at+26:at+32])
    end=head+OUTPUT['RECEIPT_BASE']+len(data['receipts'])*OUTPUT['RECEIPT_WORDS']
    assert not any(block[end:head+OUTPUT['RECEIPT_BASE']+OUTPUT['RECEIPTS']*OUTPUT['RECEIPT_WORDS']])
    # Preserve raw fractional credits and each current ADD pool. Public totals
    # are checked independently, without replacing any existing native field.
    account=L['DAMAGE_ACCOUNTING_STATE_BASE']
    raw=[data['final_scored_damage'].get(name,0.) for name in case['names']]
    assert [number(account+30+i*2) for i in range(5)]==raw
    assert number(L['WORLD_ACTOR_POOL_OUTPUT_BASE']+16)==data['final_overkill']
    assert [round(value) for value in raw]==[data['public_summary']['add_char_total'][name] for name in case['names']]
    for row in data['final_adds']:
        at=L['WORLD_ACTOR_POOL_STATE_BASE']+slots[row['label']]*16
        assert block[at]==row['generation']
        if row['generation']==0:
            assert not any(block[at:at+16]);continue
        assert list(block[at+1:at+4])==[int(row['alive']),{'':0,'처치':1,'퇴장':2,'자폭':3}[row['gone']],row['hits']]
        assert number(at+4)==row['dealt'] and number(at+6)==0. and number(at+8)==row['born']
        assert block[at+10]==row['order'] and not any(block[at+11:at+16])
    clean=list(block)
    clean[head:head+OUTPUT['RECEIPT_BASE']+OUTPUT['RECEIPTS']*OUTPUT['RECEIPT_WORDS']]=[0]*(OUTPUT['RECEIPT_BASE']+OUTPUT['RECEIPTS']*OUTPUT['RECEIPT_WORDS'])
    return clean


def compare(block,domain):
    assert len(block)==suite.OUTPUT and block[0]==0
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:native=native_reference(domain)
    clean=compare_healing(block,domain,native)
    base.compare_observed(clean,domain,native,indices)
    return native


def validate_rejection(block,name):
    assert name.startswith('reject/enemy-healing/') and block[0]==64,(name,block[0])
