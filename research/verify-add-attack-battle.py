"""Real ADD sources feed the one shared incoming damage and battle executor."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
spec=importlib.util.spec_from_file_location('add_attack_battle_parent',ROOT/'research/verify-logical-actor-geometry.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_add_attack_battle_cases import fixtures
from portable_add_attack_battle_wire import LAYOUT as A
from world_add_attack_battle_native import prepare_case,observe
from portable_specs import LIMITS as L
from portable_skill_history import require_capacity
SOURCE='gpu/world_add_attack_battle_entry.slang';STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=A['INPUT_WORDS'],OUTPUT=A['OUTPUT_WORDS']);cross=base.cross;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT


def prepare():
    rows=[]
    for c in fixtures():
        words,domain=prepare_case(c);rows.append((c['name'],words,domain))
    seed=rows[0][1]
    for label,at,value in [('magic',0,0),('version',1,2),('nodes',2,33),('actors',3,128),('reserved',4,1),('slots',16,127),('hits',17,0x80000000),('interval-nan',19,0x7ff80000),('payload-kind',24,0),('payload-atk-nan',33,0x7ff80000),('unused-row',40,1)]:
        w=list(seed);w[A['BASE']+at]=value;rows.append(('reject/add-attack-battle/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()


def native_reference(domain):
    n=observe(domain);identity=n['original_input_identity'];scenario=domain[0]['add_attack_contract']['scenario']
    assert identity['definitions']==70 and identity['chars_config_seed_weapon_verified']
    queued=n['queued_add_attacks'];hits=n['battle']['hits'];assert queued and hits and all(not h['down'] for h in hits)
    assert len(hits)==len(queued)*(2 if scenario in ('random','slots-pierce') else 5)
    if scenario=='dead':assert len(queued)==2,'Real HP death stops later ADD firing'
    if scenario=='renewal':assert {r['generation'] for r in queued}=={1,2}
    if scenario=='interleaved':assert [r['node'] for r in queued[:4]]==[0,0,1,2]
    require_capacity(n);return n


def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    assert len(block)==suite.OUTPUT and block[0]==0
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    h=A['OUTPUT_BASE'];assert block[h]==0x41444231 and block[h+1]==len(n['queued_add_attacks'])
    assert not any(block[h+2:h+A['STATE_BASE']])
    for slot,b in enumerate(domain[2]):
        at=h+A['STATE_BASE']+slot*2
        if int(b.kind)!=5:assert not any(block[at:at+2]);continue
        rows=[r for r in n['queued_add_attacks'] if r['slot']==slot]
        if not rows:assert not any(block[at:at+2]);continue
        generation=rows[-1]['generation']
        assert list(block[at:at+2])==[generation,sum(r['generation']==generation for r in rows)]
    assert not any(block[h+A['STATE_BASE']+len(domain[2])*2:h+A['MAP_BASE']])
    records=[];head=L['WORLD_FRAME_OUTPUT_BASE']
    def number(at):
        import struct
        return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    for i in range(block[head+2]):
        at=head+2832+i*6;slot,generation=block[h+A['MAP_BASE']+i*2:h+A['MAP_BASE']+(i+1)*2]
        if block[at]!=3:assert slot==generation==0;continue
        records.append(dict(node=block[at+1],slot=slot,generation=generation,index=block[at+2],time=number(at+3)))
    assert records==n['queued_add_attacks'],'Actual actor slot/generation must reach the original ordered incoming queue'
    assert not any(block[h+A['MAP_BASE']+block[head+2]*2:h+A['MAP_BASE']+A['MAP_ROWS']*2])
    clean=list(block);clean[h:h+A['MAP_BASE']+A['MAP_ROWS']*2]=[0]*(A['MAP_BASE']+A['MAP_ROWS']*2)
    return base.compare_observed(clean,domain,n,indices)


def validate_rejection(block,name):assert name.startswith('reject/add-attack-battle/') and block[0]==64
