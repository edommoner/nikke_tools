"""Private physical-interrupt diagnostic wire; no canonical Impact conversion."""
import struct
BASE=770976
COUNT=128
WORDS=32
MAGIC=0x49415231


def gpu_records(block,names):
    head=list(block[BASE:BASE+16]);count=head[1]
    assert head[0]==MAGIC and count<=COUNT and not any(head[2:]),'interrupt diagnostic header'
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    rows=[]
    for i in range(count):
        at=BASE+16+i*WORDS;row=block[at:at+WORDS]
        assert row[0]<5 and row[3] in (0,1) and row[4] in (0,1) and row[7]==0 and not any(row[24:]),'private receipt fields'
        handle=dict(identity=row[1],generation=row[2],kind=6)
        assert row[2]>0,'interrupt generation'
        rows.append(dict(attacker=names[row[0]],target=handle,label=None,time=number(at+8),damage=number(at+10),
                         before=dict(handle=handle,alive=bool(row[3]),hits=row[5],dealt=number(at+12),landed=number(at+16)),
                         after=dict(handle=handle,alive=bool(row[4]),hits=row[6],dealt=number(at+14),landed=number(at+18)),
                         accounted_before=number(at+20),accounted_after=number(at+22),canonical_credit=0))
    assert not any(block[BASE+16+count*WORDS:BASE+16+COUNT*WORDS]),'unexpected private receipt tail'
    return rows
