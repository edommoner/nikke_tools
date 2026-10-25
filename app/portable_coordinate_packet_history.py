"""Lossless ordered packet proof: unchanged raw prefix plus full-stream SHA-256."""
import hashlib,struct
from pathlib import Path
from portable_arena_specs import coordinate_layout,regions,Region,audit_regions
CP=coordinate_layout(1048576)
HEAD=CP['END'];WORDS=64;MAX_RECORDS=1048576;MAGIC=0x43504831

def audit_arena():
    rows,iw,ow=regions('combined-v1');tail=next(r for r in rows if r.name=='coordinate-clear-tail')
    assert tail.base==HEAD and WORDS<=tail.words and HEAD+WORDS<=1310720
    rows=[r for r in rows if r is not tail]+[Region('output','coordinate-packet-history',HEAD,WORDS),Region('output','coordinate-clear-tail',HEAD+WORDS,tail.words-WORDS)]
    audit_regions(rows,iw,ow)
    return dict(base=HEAD,words=WORDS,end=HEAD+WORDS,next_live_arena=1310720,raw_prefix_capacity=CP['TRACE_COUNT'],stream_capacity=MAX_RECORDS)

def schema():
    return '// Generated packet history ownership; CP_END begins the clear-tail gap.\nstatic const uint CPH_BASE=CP_END,CPH_WORDS=64,CPH_MAX=1048576,CPH_MAGIC=0x43504831U;\n'

def expected(rows):
    if len(rows)>MAX_RECORDS:raise ValueError('Ordered packet proof capacity exceeded')
    flat=[];hasher=hashlib.sha256()
    for row in rows:
        if len(row)!=12 or any(type(v) is not int or not 0<=v<2**32 for v in row):raise ValueError('Invalid packet history row')
        if row[0]>=5 or row[1]>=128 or row[2]>6 or not 0<row[3]<2**31 or row[8]>1 or any(row[9:]):raise ValueError('Invalid packet identity/flags')
        raw=struct.pack('<12I',*row);hasher.update(raw);flat.extend(row)
    digest=list(struct.unpack('>8I',hasher.digest()));pending=len(flat)%16
    swap=lambda n:int.from_bytes(n.to_bytes(4,'little'),'big')
    pad=[swap(v) for v in flat[-pending:]] if pending else []
    pad+=[0x80000000];pad+=[0]*(14-len(pad));pad+=[0,len(rows)*384]
    head=[MAGIC,1,len(rows),CP['TRACE_COUNT'],12,MAX_RECORDS,1,pending,*digest,*pad,*digest,*(rows[-1] if len(rows)>CP['TRACE_COUNT'] else [0]*12),*[0]*12]
    assert len(head)==WORDS
    return flat,head,hasher.hexdigest()

def verify(block,rows):
    audit_arena();flat,head,digest=expected(rows);retained=min(len(rows),CP['TRACE_COUNT'])
    if block[CP['BASE']+2]!=retained:raise ValueError('Packet raw-prefix count mismatch')
    if list(block[CP['TRACE']:CP['TRACE']+retained*12])!=flat[:retained*12]:raise ValueError('Packet raw-prefix words mismatch')
    if any(block[CP['TRACE']+retained*12:CP['TRACE']+CP['TRACE_COUNT']*12]):raise ValueError('Unused packet prefix is not zero')
    if list(block[HEAD:HEAD+WORDS])!=head:raise ValueError('Full ordered packet SHA/state mismatch')
    return dict(records=len(rows),raw_prefix_records=retained,streamed_records=len(rows)-retained,sha256=digest,all_ordered_packet_words_verified=True)
