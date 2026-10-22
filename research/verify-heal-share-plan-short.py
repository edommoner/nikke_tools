"""Literal independent plan/rounding cases; same adapter for Metal and CUDA."""
import array,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('heal_plan_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=520,OUTPUT=786432)
CASES=[
    ('fallback',[],2,.1,[0,0,1,0,0],[0,0,.1,0,0]),
    ('all',[31],0,5000,[1]*5,[1000]*5),
    ('chain',[3,30],0,6000,[1,2,1,1,1],[1000,2000,1000,1000,1000]),
    ('disconnected',[3,24],0,6000,[1,1,0,0,0],[3000,3000,0,0,0]),
    ('distinct-carriers',[3,3],0,.1,[2,2,0,0,0],[.05,.05,0,0,0]),
    ('multiply-before-divide',[7,3],0,.1,[2,2,1,0,0],[.04,.04,.02,0,0]),
    ('single-direct',[1,1,1],0,.1,[3,0,0,0,0],[.1,0,0,0,0]),
    ('capacity512',[31]*512,4,5,[512]*5,[1]*5),
    ('reject-mask',[32],0,1,None,None),
    ('reject-capacity',[31]*513,0,1,None,None),
]
def bits(value):return list(struct.unpack('<II',struct.pack('<d',value)))
def native_reference(domain):
    _,_,_,_,weights,parts=domain
    if weights is None:return [64]
    packed=sum(w<<(i*10) for i,w in enumerate(weights))
    return [0,sum(weights),sum(w!=0 for w in weights),packed&0xffffffff,packed>>32,*weights,*[word for part in parts for word in bits(part)],1,1]
def prepare():
    entries=[];packed=array.array('I',[len(CASES)])
    for domain in CASES:
        name,masks,original,amount,_,_=domain;words=[len(masks),original,*bits(amount),*masks]
        words.extend([0]*(suite.INPUT-len(words)));assert len(words)==suite.INPUT
        entries.append(('heal-plan-'+name,words,domain if domain[-1] is not None else None));packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def compare(block,domain):
    expected=native_reference(domain)
    assert list(block[:len(expected)])==expected,(domain[0],list(block[:len(expected)]),expected)
    assert not any(block[len(expected):]),'Unexpected plan probe output'
    return expected
def validate_rejection(block,name):
    assert name in ('heal-plan-reject-mask','heal-plan-reject-capacity')
    assert block[0]==64 and not any(block[1:]),'Wrong plan rejection or partial output'
