"""Versioned complete record chain: SHA256(previous32 bytes || LE20-word record)."""
import hashlib,struct
from portable_heal_charge_specs import TRACE_BASE,TRACE_COUNT,TRACE_WORDS,TRACE_MAGIC,TRACE_MAX
TAIL=TRACE_BASE+8+TRACE_COUNT*TRACE_WORDS
MAGIC=0x48434831

def digest(rows):
    state=bytes(32)
    for row in rows:
        assert len(row)==20
        state=hashlib.sha256(state+struct.pack('<20I',*row)).digest()
    return state

def verify(block,rows):
    count=len(rows);assert 0<=count<=TRACE_MAX
    header=[TRACE_MAGIC if count else 0,min(count,TRACE_COUNT),count,0,0,0,0,0]
    if count>TRACE_COUNT:header[3:]=[MAGIC,1,TRACE_COUNT,count-TRACE_COUNT,TRACE_WORDS]
    assert list(block[TRACE_BASE:TRACE_BASE+8])==header,('heal-charge-header',list(block[TRACE_BASE:TRACE_BASE+8]),header)
    for index,row in enumerate(rows[:TRACE_COUNT]):
        at=TRACE_BASE+8+index*TRACE_WORDS
        assert list(block[at:at+TRACE_WORDS])==row,('heal-charge-event',index,list(block[at:at+TRACE_WORDS]),row)
    if count>TRACE_COUNT:assert struct.pack('>8I',*block[TAIL:TAIL+8])==digest(rows),'complete healing record chain'
    else:assert not any(block[TAIL:TAIL+8]),'short history retains the old zero tail'
    return dict(total=count,raw_retained=min(count,TRACE_COUNT),raw_omitted=max(0,count-TRACE_COUNT),complete_order_and_quantities_verified=True,clocks_included=True)
