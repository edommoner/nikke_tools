"""Independent big-integer bitstream oracle; all output words are compared."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('interrupt_codec_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=136,OUTPUT=786432)
TAG=0x49525001

def case(name,order=(),*,birth=0xffffffff,low=0,high=0x80000000,reach=4,frozen=1,mutation=0,reuse=0,count=None):
    return dict(name=name,order=list(order),birth=birth,low=low,high=high,reach=reach,frozen=frozen,mutation=mutation,reuse=reuse,count=len(order) if count is None else count)
CASES=[case('rotate-'+str(i),[(j+i)%128 for j in range(128)]) for i in range(128)]
CASES += [case('count-'+str(i),list(reversed(range(128)))[:i],birth=0x80000000) for i in (0,1,4,5,31,32,33,127)]
CASES += [case('reuse-empty',reuse=1),case('reuse-tail',[127],reuse=1,low=0x89abcdef,high=0x01234567),case('direct',birth=0,frozen=0),case('reuse-direct',birth=0,frozen=0,reuse=1)]
CASES += [case('bad-count',count=129),case('bad-slot',[128]),case('duplicate',[7,7]),case('bad-reach',reach=5),case('bad-frozen',frozen=2),case('direct-birth',birth=1,frozen=0),case('direct-order',[1],birth=0,frozen=0)]
CASES += [case('mutate-'+str(i),[0,1],birth=0,mutation=i) for i in range(1,7)]
CASES += [case('mutate-direct-birth',birth=0,frozen=0,mutation=7)]
BY_NAME={'interrupt-codec-'+c['name']:c for c in CASES}
def admissible(c):
    return c['count']<=128 and len(c['order'])>=c['count'] and all(0<=v<128 for v in c['order']) and len(set(c['order']))==len(c['order']) and c['reach']<=4 and c['frozen'] in (0,1) and (c['frozen'] or c['count']==c['birth']==0)
def encode(c):
    values=c['order'][:c['count']];bits=sum(slot<<(7*i) for i,slot in enumerate(values));membership=sum(1<<slot for slot in values)
    return [c['count'],c['birth'],*[(membership>>(32*i))&0xffffffff for i in range(4)],*[(bits>>(32*i))&0xffffffff for i in range(28)],c['low'],c['high'],c['reach'],TAG|(2 if c['frozen'] else 0)]
def expected_block(c):
    b=array.array('I',[0])*suite.OUTPUT
    if not admissible(c):b[0]=64;return b
    record=encode(c);m=c['mutation']
    if m==1:record[37]^=4
    elif m==2:record[2]^=1
    elif m==3:record[6]^=127
    elif m==4:record[0]=129
    elif m==5:record[36]=5
    elif m==6:record[33]^=0x80000000
    elif m==7:record[1]=1
    b[8:46]=array.array('I',record)
    if m:b[0]=64
    else:b[64:64+c['count']]=array.array('I',c['order'])
    return b
def native_reference(c):return dict(count=c['count'],birth=c['birth'],order=c['order'],amount=[c['low'],c['high']],reach=c['reach'],frozen=c['frozen'])
def prepare():
    entries=[];packed=array.array('I',[len(CASES)])
    for c in CASES:
        words=[c['count'],c['birth'],c['low'],c['high'],c['reach'],c['frozen'],c['mutation'],c['reuse'],*c['order'],*([0]*(128-len(c['order'])))];assert len(words)==suite.INPUT
        domain=c if admissible(c) and not c['mutation'] else None
        entries.append(('interrupt-codec-'+c['name'],words,domain));packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def compare(block,domain):
    if array.array('I',block)!=expected_block(domain):raise AssertionError((domain['name'],'whole packet output or neighbor differs'))
    return native_reference(domain)
def validate_rejection(block,name):
    if array.array('I',block)!=expected_block(BY_NAME[name]):raise AssertionError((name,'wrong rejection or partial write'))
