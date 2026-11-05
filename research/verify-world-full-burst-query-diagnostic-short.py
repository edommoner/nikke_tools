"""Read-only ordered buff/reference/HP observations from the separate bank."""
import importlib.util,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('full_query_diag_base',ROOT/'research/verify-world-full-burst-query-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
prepare,native_reference,suite,cross=base.prepare,base.native_reference,base.suite,base.cross
from portable_specs import LIMITS as L

def decoded(block,domain):
    h=L['NATIVE_DIAG_BASE'];assert block[h]==0x46425131 and block[h+3]==0 and block[h+1]==block[h+2] and list(block[h+8:h+10])==[12,128]
    def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    rows=[]
    for i in range(block[h+1]):
        at=h+16+i*12;kind,row,owner,present=block[at:at+4];assert domain[0]['effects'][row]['name']=='landing' and owner==0
        r=dict(kind=kind,time=number(at+4))
        if kind==1:r.update(flat=number(at+6),percent=number(at+8))
        elif kind==2:r.update(present=bool(present),value=number(at+6))
        else:assert kind==3;r.update(maximum=number(at+6))
        rows.append(r)
    return rows
def compare(block,domain):
    expected=base.compare(block,domain);actual=decoded(block,domain);assert actual==expected['full_burst_query'],(domain[0]['name'],actual,expected['full_burst_query']);return expected
def validate_rejection(block,name):base.validate_rejection(block,name)
