"""Every link, timestamp, trace word and padding word is accounted for."""
import struct
from portable_lock_packet_layout import *

def bits(value):return list(struct.unpack('<II',struct.pack('<d',value)))

def compare(block,native,meta):
    if any(block[TOKENS:SHOT_TIMES]):raise AssertionError('Live packet link leaked after queue drain')
    shots=native['lock_shots'];want=[]
    for shot in shots:want.extend(bits(shot['time']))
    want.extend([0]*(SHOT_CAPACITY*2-len(want)))
    if list(block[SHOT_TIMES:SHOT_TIMES+SHOT_CAPACITY*2])!=want:raise AssertionError('Shot timestamp link differs')
    if any(block[SHOT_TIMES+SHOT_CAPACITY*2:HEAD]):raise AssertionError('Lock packet alignment padding changed')
    records=native['lock_packet_trace'];stores=sum(e['phase']==0 for e in records);loads=sum(e['phase']==1 for e in records)
    if len(records)>TRACE_CAPACITY:raise AssertionError('Packet diagnostic trace capacity exceeded')
    if list(block[HEAD:HEAD+16])!=[MAGIC,len(records),stores,loads]+[0]*12:raise AssertionError('Packet link trace header differs')
    for i,e in enumerate(records):
        row=next(j for j,source in enumerate(meta['binding_source_indices']) if source==e['source'])
        want=[e['phase'],e['packet'],row,e['hit'],e['hits'],e['token'],e['revision'],e['count'],*bits(e['time']),e['ordinal'],e['slot'],e['generation'],e['current'],e['status'],MAGIC]
        if list(block[TRACE+i*16:TRACE+(i+1)*16])!=want:raise AssertionError(('Actual packet snapshot link',i,list(block[TRACE+i*16:TRACE+(i+1)*16]),want))
    if any(block[TRACE+len(records)*16:OUTPUT]):raise AssertionError('Unexpected packet trace tail')
