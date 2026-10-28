"""Shared final-shot retirement plus the existing complete battle comparison."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
spec=importlib.util.spec_from_file_location('self_destruct_add_parent',ROOT/'research/verify-add-attack-battle.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_add_self_destruct_cases import fixtures
from world_add_self_destruct_battle_native import prepare_case,observe
from portable_add_self_destruct_wire import LAYOUT as S,MAGIC
from portable_add_attack_battle_wire import LAYOUT as A
from portable_specs import LIMITS as L
from portable_skill_history import require_capacity
SOURCE='gpu/world_add_self_destruct_entry.slang';STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=S['INPUT_WORDS'],OUTPUT=S['OUTPUT_WORDS']);cross=base.cross;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT


def prepare():
    rows=[]
    for c in fixtures():
        words,domain=prepare_case(c);rows.append((c['name'],words,domain))
    seed=rows[0][1];at=A['BASE']+A['ROW_BASE']
    for name,offset,value in [('flag',4,2),('delay-negative',6,0xbff00000),('delay-nan',6,0x7ff80000),('reserved',7,1),('unbounded-self',1,0),('unused-row',24+4,1)]:
        w=list(seed);w[at+offset]=value;rows.append(('reject/add-self-destruct/'+name,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()


def native_reference(domain):
    n=observe(domain);scenario=domain[0]['self_destruct_contract']['scenario'];retired=n['self_destruct'];queued=n['queued_add_attacks']
    assert n['original_input_identity']['chars_config_seed_weapon_verified']
    if scenario in ('hp-before-shot','time-close'):assert not retired and not queued
    else:
        count=6 if scenario=='EH-death-resources' else 4 if scenario=='renewal' else 2
        assert len(retired)==count and queued
        for r in retired:
            hits=[h for h in queued if h['slot']==r['slot'] and h['generation']==r['generation']]
            assert hits and hits[-1]['time']==r['time'] and hits[-1]['index']==r['fired']-1
        if scenario=='renewal':assert {r['generation'] for r in retired}=={1,2}
    if scenario=='EH-death-resources':
        assert n['original_resources']['dispatches'],'Original enemy-death resource effects must execute'
    require_capacity(n);return n


def compare(block,domain):
    import struct
    from world_coordinate_sampled_skill_native import creation_indices
    assert len(block)==suite.OUTPUT and block[0]==0
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    head=S['OUTPUT_BASE'];count=block[head+1]
    assert block[head]==MAGIC and count==block[head+2]==len(n['self_destruct']) and not any(block[head+3:head+16])
    for i,r in enumerate(n['self_destruct']):
        at=head+S['HEADER']+i*S['ROW_WORDS'];node,slot,generation,fired=block[at:at+4]
        time=struct.unpack('<d',struct.pack('<II',*block[at+4:at+6]))[0]
        assert dict(time=time,node=node,slot=slot,generation=generation,fired=fired)==r
        record=block[at+6];w=L['WORLD_FRAME_OUTPUT_BASE']+2832+record*6
        assert block[w:w+3]==[5,node,slot] and list(block[w+3:w+5])==list(block[at+4:at+6])
        assert block[at+7]==1 and not any(block[at+8:at+12])
    end=head+S['HEADER']+S['ROWS']*S['ROW_WORDS'];assert not any(block[head+S['HEADER']+count*S['ROW_WORDS']:end])
    clean=list(block);clean[head:end]=[0]*(end-head)
    base.compare_observed(clean,domain,n,indices)
    spec=importlib.util.spec_from_file_location('self_destruct_resource_parent',ROOT/'research/verify-coordinate-original-resources-short.py');resources=importlib.util.module_from_spec(spec);spec.loader.exec_module(resources)
    resources.compare_resource_state(clean,domain,n)
    return n


def validate_rejection(block,name):assert name.startswith('reject/add-self-destruct/') and block[0]==64
