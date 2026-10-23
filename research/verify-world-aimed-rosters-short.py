"""Complete real profiles and literal target worlds through the shared executor."""
import array,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from world_real_aim_native import real,observe
from portable_real_aim_policy import configured
from portable_aimed_roster_cases import fixtures
from portable_projectile_roster_input import compile_projectile_battle
from portable_specs import LIMITS as L
from portable_ordered_history import verify_history,friendly_records
from portable_revival_specs import RNG
from portable_interrupt_specs import pool_bindings
from calculator.boss_pattern import validate,AIM_ADDS
import engine_worker
spec=importlib.util.spec_from_file_location('real_aim_common_suite',ROOT/'research/verify-world-aimed-area-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross


def prepare():
    entries=[]
    for case in fixtures():
        with configured(case['body'],case['aim_policy']):prepared=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,metadata=compile_projectile_battle(prepared,allow_physical_interrupt=True)
        entries.append((case['name'],words,(case,prepared,words,metadata)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    from portable_aimed_roster_contracts import verify
    native=observe(domain[0]);verify(domain[0],native);return native


def compare(block,domain):
    case,prepared,words,metadata=domain;expected=native_reference(domain)
    assert block[0]==0,(case['name'],'GPU status',block[0])
    _,_,omitted,diff=real.compare(block,prepared,(words,metadata),expected['battle'],expected['physical_shots'])
    assert not diff,(case['name'],'unfiltered real battle',diff[:8])
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    bindings=sorted(pool_bindings(validate(case['body']['enemy']['patterns'],squad_size=5)),key=lambda b:(int(b.kind),b.identity))
    h=L['WORLD_ACTOR_POOL_OUTPUT_BASE'];p=L['WORLD_ACTOR_POOL_STATE_BASE'];o=L['WORLD_OVERLAY_STATE_BASE']
    pools=dict(pools=[list(block[p+i*16:p+(i+1)*16]) for i in range(len(bindings))],score=block[h+8]+(block[h+9]<<32),spawned=block[h+4],overkill=number(h+16),notice_counts=list(block[h+10:h+14]),pending_notices=block[h+5],deaths=block[h+14])
    assert pools==expected['target_world']['actor_pools'],(case['name'],'all target pools',pools,expected['target_world']['actor_pools'])
    nodes=[dict(blocked=number(o+32+i*8+4),opens=block[o+32+i*8]) for i in range(len(case['body']['enemy']['patterns']))]
    assert nodes==expected['target_world']['world_nodes'],(case['name'],'world nodes')
    assert [number(785424+i*2) for i in range(5)]==expected['target_world']['interrupt_damage'],(case['name'],'complete interrupt damage')
    extra=[]
    for slot,b in enumerate(bindings):
        gen=block[p+slot*16]
        if int(b.kind)!=6 or gen==0:continue
        at=L['COUNTER_LANDING_EXTRA_BASE']+slot*4
        extra.append(dict(identity=b.identity,generation=gen,extra_hits=block[at],extra_dealt=number(at+2)))
    assert extra==expected['target_world']['extra'],(case['name'],'interrupt reach extras')
    head=L['FOCUS_STATE_BASE'];bits=block[head]|block[head+1]<<32;labels={0:'',128:AIM_ADDS,**{i:b.label for i,b in enumerate(bindings) if i}}
    focus=dict(aims=[labels[(bits>>(8*i))&255] for i in range(5)],camera=block[head+2],full_burst=bool(block[head+3]))
    assert focus==expected['target_world']['focus'],(case['name'],'final focus',focus,expected['target_world']['focus'])
    samples=expected['friendly_samples'];verify_history(block,friendly_records(samples))
    if samples:
        state=(3,tuple(block[RNG+8:RNG+632])+(block[RNG],),None)
        digest=hashlib.sha256(json.dumps(state,separators=(',',':')).encode()).hexdigest()
        assert digest==samples[-1]['after_sha256'],(case['name'],'complete final MT state')
    return expected


def validate_rejection(block,name):raise AssertionError('No raw rejection in real aimed roster suite')
