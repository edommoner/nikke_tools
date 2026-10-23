"""All recipient masks at each native shot; diagnostic only uses reserved trace words."""
import array,importlib.util,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('named_enemy_diagnostic_base',Path(__file__).with_name('verify-world-named-enemy-short.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross,native_reference=base.suite,base.cross,base.native_reference
from portable_revival_specs import BASE,TRACE,TRACE_COUNT

def prepare():
    rows=[r for r in base.prepare()[0] if r[2] is not None];packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def compare_trace(block,domain):
    c,_,bindings=domain;expected=c['contract']['picked'];count=block[BASE+6]
    assert count==len(expected)<=TRACE_COUNT,(c['name'],'trace count',count)
    for i,picked in enumerate(expected):
        at=TRACE+i*8;record=list(block[at:at+8]);mask=[0]*4
        for label in picked:
            slots=[j for j,b in enumerate(bindings) if b.label==label];assert len(slots)==1,(label,slots)
            j=slots[0];mask[j//32]|=1<<(j%32)
        assert record==[0x4e455431,len(c['effects'])-1,*mask,len(picked),0],(c['name'],i,record,picked)
def compare(block,domain):
    expected=base.compare(block,domain);compare_trace(block,domain);return expected
def validate_rejection(block,name):raise AssertionError('No diagnostic rejection inputs')
