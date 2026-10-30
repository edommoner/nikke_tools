"""Complete original battle comparison with an opt-in independent cover layer."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('cover_original_comparison',ROOT/'research/verify-original-catalogue.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_cover_defense_wire import INPUT,OUTPUT,LAYOUT,SOURCE,compile_cover
from portable_cover_defense_battle_cases import fixtures
from portable_cover_defense_battle_contracts import verify
from portable_original_catalogue_cases import prepare as original_prepare
from cover_defense_battle_model import cover_defense
suite=SimpleNamespace(INPUT=INPUT,OUTPUT=OUTPUT);cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows=[]
    for row in fixtures():
        c,p=original_prepare(row);c['cover_defense_case']={k:copy.deepcopy(row[k]) for k in ('name','contract','patterns','cover_defense')}
        w,m,b,d=compile_cover(p,row);rows.append((c['name'],w,(c,m,b,d)))
    seed=rows[0][1]
    for label,offset,value in [('magic',0,0),('version',1,2),('owners',2,4),('reserved',3,1),('tail',23,1),('nonfinite-base',9,0x7ff00000),('negative-base',9,0xbff00000)]:
        w=list(seed);w[LAYOUT['BASE']+offset]=value;rows.append(('reject/cover-defense/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def compare_receipts(block,domain,native):
    head=LAYOUT['OUTPUT_BASE'];data=native['cover_defense'];rows=data['receipts'];names=domain[0]['names']
    assert list(block[head:head+2])==[0x43444231,len(rows)] and not any(block[head+2:head+LAYOUT['RECEIPT_BASE']])
    for i,r in enumerate(rows):
        at=head+LAYOUT['RECEIPT_BASE']+i*32
        assert list(block[at:at+2])==[names.index(r['name']),r['divisor']]
        for offset,key in [(2,'time'),(4,'attack'),(6,'coefficient'),(8,'received_snapshot'),(10,'base_defense'),(12,'effective_defense'),(14,'quantity'),(16,'shared_quantity'),(18,'hp_before'),(20,'applied'),(22,'hp_after')]:
            assert list(block[at+offset:at+offset+2])==list(struct.unpack('<II',struct.pack('<d',r[key]))),(i,key)
        assert not any(block[at+24:at+32])
    assert not any(block[head+LAYOUT['RECEIPT_BASE']+len(rows)*32:])

def compare(block,domain):
    # Reuse the original full battle / physical / typed / history comparison.
    # Only the new declaration/receipt suffix is separated from the old arena.
    with patch.object(base,'native_reference',native_reference):n=base.compare(block[:LAYOUT['OUTPUT_BASE']],domain)
    compare_receipts(block,domain,n);return n

# Avoid recursion while base.compare resolves its own reference symbol.
_original_native_reference=base.native_reference

def native_reference(domain):
    case=domain[0]['cover_defense_case']
    with cover_defense(case['cover_defense'],case['contract']['names']) as data:n=_original_native_reference(domain)
    n['cover_defense']=data;verify(case,n);return n

def validate_rejection(block,name):
    assert name.startswith('reject/cover-defense/') and block[0]==64
