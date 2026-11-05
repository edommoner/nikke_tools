"""Reuse all88 sealed cases and the same shared Frame/source for hit credit."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_hit_shield_cases import fixtures
s=importlib.util.spec_from_file_location('hit_shield_base',ROOT/'research/verify-destructible-shield-battle-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite=base.suite;cross=base.cross;native_reference=base.native_reference;compare=base.compare

def compile_case(c):
    w,domain=base.compile_case(c)
    if c.get('hit_shield_interception_v1'):
        w[110080]=0x48534932;w[110084]=1
        for row in range(256):
            if w[109824+row]==3:w[109824+row]=4
    return w,domain

def prepare():
    rows=base.prepare()[0];rows.extend((c['name'],*compile_case(c)) for c in fixtures());seed=rows[88][1]
    for label,offset,value in [('policy-version',110080,0x48534931),('policy-flag',110084,0),('policy-reserved',110085,1),('unknown-route',109825,5),('nonintegral-hit-capacity',104400+2332,0x3ff80000)]:
        w=list(seed);w[offset]=value;rows.append(('reject/destructible-hit-shield/'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def validate_rejection(block,name):
    if name.startswith('reject/destructible-hit-shield/'):assert block[0]==64,(name,block[0])
    else:base.validate_rejection(block,name)
