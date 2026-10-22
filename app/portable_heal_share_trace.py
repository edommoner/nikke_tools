"""Project actual native call records into a strict diagnostic GPU wire trace.

The observer-only HP-notify stream is excluded explicitly; full battle state
and the existing skill trace remain compared separately. Unobserved source
identities in old cases are projected to the same unknown sentinel on read.
"""
import struct
BASE=771072
COUNT=512
WORDS=20
MAGIC=0x48534831
KINDS={'shared-call':1,'plan':2,'portion-call':3,'portion-return':4,'shared-return':5,'notify':6,'lifesteal-call':7}
def bits(value):return list(struct.unpack('<II',struct.pack('<d',value)))
def native_records(events):
    records=[]
    for event in events:
        kind=event['kind']
        if kind=='notify' and event['event']!='event:heal_received':continue
        row=[0]*WORDS;row[:3]=[KINDS[kind],event['owner'],event.get('heal_source',0xffffffff)]
        row[3:5]=bits(event['time'])
        row[5:7]=bits(event.get('damage',event.get('after',event.get('amount',0))))
        if kind=='plan':
            packed=0
            for who,weight in event['weights']:
                assert 0<=who<5 and 1<=weight<=512
                packed|=weight<<(who*10)
            row[7:9]=[packed&0xffffffff,packed>>32]
        if kind in ('shared-call','shared-return'):row[9:19]=[v for hp in event['hp'] for v in bits(hp)]
        records.append(row)
    assert len(records)<=COUNT
    return records
def gpu_records(block,*,observe_heal_sources):
    head=list(block[BASE:BASE+8]);count=head[1]
    assert count<=COUNT and head[2:]==[0]*6 and head[0] in (0,MAGIC)
    assert head[0]==MAGIC or count==0
    rows=[list(block[BASE+8+i*WORDS:BASE+8+(i+1)*WORDS]) for i in range(count)]
    for row in rows:
        assert 1<=row[0]<=7 and row[1]<5 and row[19]==0
        if row[0]==6 and not observe_heal_sources:row[2]=0xffffffff
    assert not any(block[BASE+8+count*WORDS:BASE+8+COUNT*WORDS]),'Unexpected diagnostic tail'
    return rows
