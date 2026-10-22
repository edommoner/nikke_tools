"""Decode a bounded observation stream; never use it as GPU calculation input."""
import math,struct
from portable_specs import LIMITS as L
LOWER,UPPER=13.3,13.37


def decode(block):
    head=L['NATIVE_DIAG_BASE']
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    assert block[head]==0x4e514431 and list(block[head+8:head+10])==[16,256],'numeric query diagnostic identity'
    count,total,omitted=block[head+1:head+4]
    assert count==min(total,256) and omitted==total-count,'numeric query diagnostic bounds'
    assert number(head+4)==LOWER and number(head+6)==UPPER and not any(block[head+10:head+16]),'numeric query diagnostic window'
    rows=[]
    for i in range(count):
        at=head+16+i*16;kind,who,target,exclusion,epoch,phase=block[at:at+6]
        when,flat,percent=number(at+6),number(at+8),number(at+10)
        assert kind in (1,2) and who<5 and phase<=5 and LOWER<=when<=UPPER
        assert all(math.isfinite(v) for v in (when,flat,percent))
        assert block[at+12]<=624 and not any(block[at+14:at+16]),'diagnostic RNG/reserved fields'
        rows.append(dict(hit=kind==1,owner=who,target=target,exclusion=exclusion,epoch=epoch,
                         phase=phase,time=when,atk_flat=flat,atk_pct=percent,after_index=block[at+12],sample_total=block[at+13]))
    assert not any(block[head+16+count*16:head+L['NATIVE_DIAG_WORDS']]),'diagnostic unused tail'
    return dict(rows=rows,total=total,omitted=omitted,window=[LOWER,UPPER])


def native_misses(queries,names):
    rows=[]
    for q in queries:
        if q['hit'] or not LOWER<=q['time']<=UPPER:continue
        assert q['target']=='__enemy__' and not q['exclude'],'This diagnostic comparator requires the body/empty-exclusion view'
        rows.append(dict(owner=q['owner'],target=0,exclusion=0,time=q['time'],
                         atk_flat=q['buffs'].get('atk_flat',0.),atk_pct=q['buffs'].get('atk_pct',0.),after_index=q['after_index'],
                         sample_total=q['sample_total']))
    return rows


def compare_misses(actual,expected):
    assert actual['omitted']==0,'numeric query diagnostic overflow'
    keys=('owner','target','exclusion','time','atk_flat','atk_pct','after_index','sample_total')
    gpu=[{k:r[k] for k in keys} for r in actual['rows'] if not r['hit']]
    diffs=[dict(index=i,gpu=a,native=b) for i,(a,b) in enumerate(zip(gpu,expected)) if a!=b]
    assert len(gpu)==len(expected) and not diffs,dict(gpu_misses=len(gpu),native_misses=len(expected),first=diffs[:8])


def decode_census(block):
    head=L['NATIVE_DIAG_BASE']
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    assert block[head]==0x4e514331 and list(block[head+8:head+10])==[2,2048],'query census identity'
    count,total,omitted=block[head+1:head+4]
    assert count==min(total,2048) and omitted==total-count and omitted==0,'query census bounds'
    assert not any(block[head+10:head+16]) and not any(block[head+16+count*2:head+L['NATIVE_DIAG_WORDS']]),'query census reserved/tail'
    rows=[dict(sample_total=block[head+16+i*2],after_index=block[head+17+i*2]) for i in range(count)]
    assert all(r['after_index']<=624 for r in rows),'query census MT index'
    return dict(rows=rows,first=number(head+4),last=number(head+6))


def native_census(queries):
    rows=[]
    for q in queries:
        if q['hit'] or q['owner']!=0 or rows and rows[-1]['time']==q['time']:continue
        rows.append(dict(time=q['time'],sample_total=q['sample_total'],after_index=q['after_index']))
    return rows


def compare_census(actual,expected):
    assert expected,'empty query census reference'
    differences=[dict(index=i,gpu=a,native=b) for i,(a,b) in enumerate(zip(actual['rows'],expected)) if a!={k:b[k] for k in a}]
    assert not differences and len(actual['rows'])==len(expected) and (actual['first'],actual['last'])==(expected[0]['time'],expected[-1]['time']),dict(gpu_count=len(actual['rows']),native_count=len(expected),gpu_endpoints=[actual['first'],actual['last']],native_endpoints=[expected[0]['time'],expected[-1]['time']],first=differences[:3],scope='First owner0 miss at each observed time; intermediate times are ordinal context, not independently certified')
