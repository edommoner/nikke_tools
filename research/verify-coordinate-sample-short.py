"""Exact CPython MT state/draw order plus the selected shared point recipe."""
import array,importlib.util,random,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_coordinate_sample_v1 as sample
from portable_coordinate_sample_cases import fixtures
n=sample.n
spec=importlib.util.spec_from_file_location('sample_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
SOURCE='gpu/coordinate_sample_probe.slang';INPUT_WORDS=24;OUTPUT_WORDS=1024;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
def words64(v):return [v&0xffffffff,v>>32]
def pack(c):return [sample.MAGIC,1,c['mode'],c['count'],*words64(c['seed']),c['skip'],c['bound'],*sum([words64(n.bits(v)) for v in [*c['aim'],c['radius'],c['k']]],[]),c['critical'],*([0]*7)]
def prepare():
    sample.check_schema(ROOT);rows=[('coordinate-sample/'+c['name'],pack(c),c) for c in fixtures()];seed=rows[0][1]
    for name,at,v in [('magic',0,0),('version',1,2),('angle-mode',2,3),('empty',3,0),('count-overflow',3,17),('skip',6,1301),('bound',7,129),('critical',16,2),('tail',23,1),('x-nan',9,0x7ff80000),('radius-inf',13,0x7ff00000),('k-zero',14,0),('k-negative',15,0xbff00000)]:
        w=list(seed);w[at]=v
        if name=='k-zero':w[15]=0
        rows.append(('reject/coordinate-sample/'+name,w,None))
    c=fixtures()[0]|dict(aim=[float.fromhex('0x1.fffffffffffffp+1023'),0.],radius=float.fromhex('0x1.fffffffffffffp+1023'),mode=0,seed=0,count=1)
    rows.append(('reject/coordinate-sample/result-overflow',pack(c),None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
class Stream(random.Random):
    def __init__(self,seed):super().__init__(seed);self.draws=0;self.rejects=0
    def getrandbits(self,k):self.draws+=1;return super().getrandbits(k)
    def below(self,bound):
        k=bound.bit_length();v=self.getrandbits(k)
        while v>=bound:self.rejects+=1;v=self.getrandbits(k)
        return v
def native_reference(c):
    rng=Stream(c['seed']);out=[0]*OUTPUT_WORDS;out[1:4]=[sample.MAGIC,1,c['count']]
    for _ in range(c['skip']):rng.getrandbits(32)
    for i in range(c['count']):
        angle=c['mode']==1 or c['mode']==2 and i%2!=0;u=sample.random53(rng);v=sample.random53(rng) if angle else None
        x,y=sample.point(*map(n.bits,[*c['aim'],c['radius'],c['k']]),u,v)
        crit=sample.random53(rng) if c['critical'] else 0;selected=rng.below(c['bound']) if c['bound'] else 0
        at=656+i*16;out[at:at+16]=[*words64(x),*words64(y),*words64(u),*words64(v or 0),*words64(crit),selected,rng.getstate()[1][-1],rng.draws,int(angle),0,0]
    state=rng.getstate()[1];out[16:24]=[state[-1],rng.draws,0,rng.rejects,0,0,0,0];out[24:648]=state[:-1]
    return dict(reference_kind='deterministic-common-cpu',contract=sample.PROFILE,contract_sha256=sample.contract_sha256(),words=out)
def compare(block,domain):
    expected=native_reference(domain);assert list(block)==expected['words'],('sample point, complete MT state/draw order or unused tail',domain['name']);return expected
def validate_rejection(block,name):assert name.startswith('reject/coordinate-sample/') and list(block)==[64]+[0]*1023
