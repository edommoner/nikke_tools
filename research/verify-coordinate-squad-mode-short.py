"""Version2 mode state joins the common squad/manual executor."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('squad_mode_parent',ROOT/'research/verify-coordinate-squad-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_squad_mode_specs import SOURCE,INPUT_BASE,MAGIC,STATE_BASE,mark
from portable_coordinate_squad_mode_cases import fixtures
INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True;suite=parent.suite;cross=parent.cross

def compile_case(case):
    w,m,b,d=parent.compile_case(case)
    return (mark(w) if case.get('squad_mode_state') else w),m,b,d

def prepare():
    rows,_=parent.prepare()
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    seed=next(w for name,w,_ in rows if name=='coordinate-squad-mode/entry-wait-exact')
    for label,offset,value in [('version',1,3),('marker',5,0),('v1-marker',1,1),('reserved',6,1),('marker-mismatch',5,MAGIC+1)]:
        w=list(seed);w[INPUT_BASE+offset]=value;rows.append(('reject/squad-mode/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):return parent.native_reference(domain)
def compare(block,domain):
    if not domain[0].get('squad_mode_state'):return parent.compare(block,domain)
    h=STATE_BASE;assert block[h+1]==2 and block[h+5]==MAGIC and block[h+29]==MAGIC
    clean=list(block);clean[h+1]=1;clean[h+5]=0;clean[h+16:h+30]=[0]*14
    n=parent.compare(clean,domain);mode=n['squad_mode_state'];assert list(block[h+16:h+21])==list(map(int,mode['flags'])),'Physical CharState mode flag'
    a=0xcbf29ce484222325;b=0x84222325cbf29ce4;mask=(1<<64)-1
    for row in mode['pumps']:
        for word in [*struct.unpack('<II',struct.pack('<d',row['time'])),row['mask']]:
            a=((a^word)*0x100000001b3)&mask;b=(((b<<7)|(b>>57))^word*0x9e3779b185ebca87)&mask
    assert list(block[h+24:h+28])==[a&0xffffffff,a>>32,b&0xffffffff,b>>32],'Every pre-pump physical mode snapshot'
    assert block[h+28]==len(mode['pumps']) and not any(block[h+21:h+24])
    return n

def validate_rejection(block,name):
    if name.startswith('reject/squad-mode/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
