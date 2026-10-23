"""Read GPU-owned pool/archive values without supplying execution quantities."""
import struct
from portable_specs import LIMITS as L

def gpu_final(block,metadata):
    carriers={}
    for i in range(block[9]):
        at=L['CARRIER_STATE_BASE']+i*L['CARRIER_WORDS'];carriers[block[at]]=(bool(block[at+4]&1),block[at+9])
    names={v:k for k,v in metadata['states'].items()};pools=[];archive={}
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    for obj in range(L['PROTECTION_OBJECTS']):
        at=L['PROTECTION_OBJECT_BASE']+obj*L['PROTECTION_OBJECT_WORDS'];flags=block[at+22];kind=flags&255
        if kind==14:archive[names[block[at+4]]]=number(at);continue
        if kind not in (13,16):continue
        slot,order=block[at+6],block[at+20]
        if carriers.get(slot)!=(True,order) or block[L['PROTECTION_MAP_BASE']+slot]!=obj+1:continue
        pools.append(dict(name=names.get(block[at+4],''),owner=(flags>>10)&7,stat='dmg_accum_dealt_atk_pct' if kind==13 else 'dmg_accum_received_atk_pct',base=number(at+2),current=number(at),done=bool(flags&262144),order=order))
    pools.sort(key=lambda p:p.pop('order'))
    return dict(pools=pools,archive=archive)

def compare_final(block,metadata,observation):
    actual=gpu_final(block,metadata);native=observation['final']
    expected=dict(pools=[{k:p[k] for k in ('name','owner','stat','base','current','done')} for p in native['pools']],archive=native['archive'])
    # float equality alone would hide signed-zero changes in stored quantities.
    def exact(value):
        if type(value) is float:return struct.pack('<d',value).hex()
        if isinstance(value,dict):return {k:exact(v) for k,v in value.items()}
        if isinstance(value,list):return [exact(v) for v in value]
        return value
    assert exact(actual)==exact(expected),('damage accumulation final state',actual,expected)
    return actual
