"""Observe final semantic pool records; never provide quantities to the GPU."""
import struct
from portable_specs import LIMITS as L

def native_final(case,observation):
    rows=[]
    for p in observation['final']:
        assert p['active'] or p['ended'] and not p['done'],('unexpected native retired record',p)
        rows.append(dict(name=case['effects'][p['row']]['name'],**{k:p[k] for k in ('owner','base','current','done','ended','active')}))
    return rows

def gpu_final(block,metadata):
    carriers={}
    for i in range(block[9]):
        at=L['CARRIER_STATE_BASE']+i*L['CARRIER_WORDS'];carriers[block[at]]=(bool(block[at+4]&1),block[at+9])
    names={v:k for k,v in metadata['states'].items()};rows=[]
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    for obj in range(L['PROTECTION_OBJECTS']):
        at=L['PROTECTION_OBJECT_BASE']+obj*L['PROTECTION_OBJECT_WORDS'];flags=block[at+22]
        if flags&255!=10:continue
        slot,order=block[at+21],block[at+20];active=carriers.get(slot)==(True,order) and block[L['PROTECTION_MAP_BASE']+slot]==obj+1
        ended,done=bool(flags&131072),bool(flags&262144)
        if not active and not (ended and not done):continue
        rows.append(dict(name=names[block[at+4]],owner=(flags>>10)&7,base=number(at+2),current=number(at),done=done,ended=ended,active=active))
    return rows

def compare_final(block,metadata,case,observation):
    expected=native_final(case,observation);actual=gpu_final(block,metadata)
    def key(p):return (p['name'],p['owner'],struct.pack('<d',p['base']),struct.pack('<d',p['current']),p['done'],p['ended'],p['active'])
    assert sorted(map(key,actual))==sorted(map(key,expected)),('healing charge final pool',actual,expected)
    return actual
