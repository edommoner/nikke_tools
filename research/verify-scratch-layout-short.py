"""Whole-output marker oracle; storage ownership, never battle certification."""
import array,hashlib,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scratch_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=4,OUTPUT=786432)
CASES=[dict(name=f'scratch-layout-{mode}-{seed:08x}',mode=mode,seed=seed,reserved=0) for mode in range(3) for seed in (0,0xffffffff)]
CASES += [dict(name='reject/scratch-mode',mode=3,seed=0,reserved=0),dict(name='reject/scratch-reserved',mode=0,seed=0,reserved=1)]


def prepare():
    rows=[(c['name'],[c['mode'],c['seed'],c['reserved'],0],None if c['name'].startswith('reject/') else c) for c in CASES]
    data=array.array('I',[len(rows)])
    for _,words,_ in rows:data.extend(words)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()


def expected(case):
    # Literal independently reviewed allocation, not the shader's address helper.
    b=array.array('I',[0])*786432;seed=case['seed']
    marker=lambda tag,i:seed^((tag*0x9e3779b9+i)&0xffffffff)
    def paint(base,count,tag,offset=0):b[base:base+count]=array.array('I',(marker(tag,offset+i) for i in range(count)))
    paint(258576,2080,1);paint(785440,32,2)
    paint(248600,32*136,3);paint(518336,32*136,3,32*136)
    paint(785472,64,4);paint(781328,4096,5);paint(785424,10,6)
    if case['mode']==1:paint(770976,4112,7)
    if case['mode']==2:paint(771072,10248,8)
    b[1:8]=array.array('I',[case['mode'],seed,64,marker(5,0),marker(5,1),marker(5,4094),marker(5,4095)])
    return b


def native_reference(case):
    return dict(proof_kind='maximum-capacity-disjoint-storage',battle_certified=False,
                mode=case['mode'],seed=case['seed'],numeric_cache_cells=64,focus_cache_cells=256,
                part_receipts=2048,output_sha256=hashlib.sha256(expected(case).tobytes()).hexdigest())


def compare(block,case):
    assert list(block)==list(expected(case)),(case['name'],'full output marker/capacity/padding mismatch')
    return native_reference(case)


def validate_rejection(block,name):
    assert name.startswith('reject/scratch-') and block[0]==64 and not any(block[1:])
