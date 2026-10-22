"""Independent hashlib oracle for both GPU targets; not a battle certification."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app')]
from portable_ordered_history import MAX_COUNT,verify_history
s=importlib.util.spec_from_file_location('history_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=4,OUTPUT=786432)
CASES=[dict(name='ordered-history-'+str(n),count=n,seed=0x12345678,enabled=1,bad_kind=0) for n in (0,1,2,127,128,129,130,255,4550,8192)]
CASES += [dict(name='reject/history-'+label,count=n,seed=0,enabled=enabled,bad_kind=bad) for label,n,enabled,bad in (('hard-cap',MAX_COUNT+1,1,0),('disabled-overflow',129,0,0),('unknown-kind',129,1,1))]


def records(case):
    rows=[]
    for i in range(case['count']):
        r=[(case['seed']^((i*0x9e3779b9+j*0x85ebca6b)&0xffffffff)) for j in range(8)]
        r[0]=1+i%3;rows.append(r)
    return rows


def prepare():
    entries=[];packed=array.array('I',[len(CASES)])
    for case in CASES:
        words=[case['count'],case['seed'],case['enabled'],case['bad_kind']]
        domain=None if case['name'].startswith('reject/') else case
        entries.append((case['name'],words,domain));packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(case):
    from portable_ordered_history import semantic_digest
    return dict(proof_kind='ordered-semantic-hash-contract',battle_certified=False,count=case['count'],semantic_sha256=semantic_digest(records(case)))


def compare(block,case):
    assert block[0]==0
    verify_history(block,records(case),prefix=8,head=2048,total=case['count'])
    assert not any(block[1:8]) and not any(block[8+min(case['count'],128)*8:2048]) and not any(block[2112:]),'probe writes outside allocated prefix/history'
    return native_reference(case)


def validate_rejection(block,name):
    assert name.startswith('reject/history-') and block[0]==64
