"""Versioned selection history: exact raw prefix and timestamp-free semantic SHA-256."""
import hashlib
import struct
from portable_specs import LIMITS as L

MAGIC=0x4f485331
PREFIX=128
MAX_COUNT=1048576


def canonical(record):
    row=list(record)
    assert len(row)==8 and row[0] in (1,2,3),'history record identity'
    for i in ((6,7) if row[0]==3 else (2,3)):
        row[i]=0
    return row


def semantic_digest(records):
    h=hashlib.sha256()
    for row in records:h.update(struct.pack('<8I',*canonical(row)))
    return h.hexdigest()


def verify_history(block,records,*,prefix=None,head=None,total=None):
    from portable_revival_specs import TRACE,BASE
    prefix=TRACE if prefix is None else prefix
    head=L['ORDERED_HISTORY_BASE'] if head is None else head
    total=block[BASE+6] if total is None else total
    assert total==len(records) and 0<=total<=MAX_COUNT,'history total count'
    retained=min(total,PREFIX)
    assert [canonical(block[prefix+i*8:prefix+(i+1)*8]) for i in range(retained)]==[canonical(r) for r in records[:retained]],'ordered raw prefix'
    digest=semantic_digest(records)
    if total<=PREFIX:
        assert not any(block[head:head+64]),'short history must retain the prior zero bank'
    else:
        assert list(block[head:head+7])==[MAGIC,1,total,PREFIX,total-PREFIX,8,1],'history version/count/finalization'
        assert block[head+7]==(total*8)%16,'history block remainder'
        assert struct.pack('>8I',*block[head+32:head+40]).hex()==digest,'complete ordered semantic history SHA-256'
        assert list(block[head+8:head+16])==list(block[head+32:head+40]),'history final state'
        padding=([int.from_bytes(struct.pack('<I',w),'big') for w in canonical(records[-1])] if total%2 else [])+[0x80000000]
        padding += [0]*(14-len(padding))+[0,total*256]
        assert list(block[head+16:head+32])==padding,'history final SHA padding'
        assert canonical(block[head+48:head+56])==canonical(records[-1]),'last raw scratch record'
        assert not any(block[head+40:head+48]) and not any(block[head+56:head+64]),'history reserved words'
    return dict(verified=True,total=total,raw_retained=retained,raw_suffix_omitted=total-retained,
                semantic_sha256=digest,complete_selection_order_verified=True,
                timestamps_in_semantic_digest=False)


def friendly_records(samples,*,owner=None,selector=None):
    rows=[]
    for sample in samples:
        caster=sample.get('owner',owner);kind=sample.get('selector',selector)
        assert caster in range(5) and kind in (19,25),'friendly history owner/selector'
        k=sample['k'];pool=sum(1<<i for i in sample['pool'])
        order=sum((who+1)<<(3*i) for i,who in enumerate(sample['picked']))
        assert 0<=k<=5 and len(sample['picked'])==k and len(set(sample['picked']))==k
        assert all(pool&(1<<who) for who in sample['picked'])
        rows.append([3,caster|(kind<<3)|(k<<8),pool,order,sample['before_index'],sample['after_index'],0,0])
    return rows
