"""Literal typed values/copy semantics; no CPU battle or GPU-derived oracle."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('definition_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=104400,OUTPUT=786432)
# owner, signed budget bits, raw binary64 bits, route, hits. These are test
# stimuli, including deliberately invalid battle metadata and NaN payload bits.
VALUES=[(4,0xffffffff,0x7ff8000000000042,7,13),(0xffffffff,0x80000000,0x8000000000000000,0,0),
        (0,0,0xffffffffffffffff,0xffffffff,0xffffffff),(17,0x7fffffff,0,1,3),
        (23,0xffffffd6,0x0010000000000000,2,19),(511,123,1,4,32)]


def prepare():
    from portable_specs import LIMITS as L,FIELDS as F
    assert suite.INPUT==L['WORLD_RELOAD_INPUT_WORDS'] and suite.OUTPUT==L['WORLD_RELOAD_OUTPUT_WORDS']
    entries=[];packed=array.array('I',[len(VALUES)])
    for index,row in enumerate(VALUES):
        second=VALUES[(index+1)%len(VALUES)];words=[0]*suite.INPUT
        overrides=(0x12345678,0xffffffff,0x87654321,0)
        words[:4]=overrides
        for number,(owner,budget,value,route,hits) in enumerate((row,second)):
            at=L['DEFINITION_BASE']+number*L['DEFINITION_WORDS'];words[at+F['OWNER']]=owner;words[at+F['BUDGET']]=budget
            words[at+F['VALUE']:at+F['VALUE']+2]=[value&0xffffffff,value>>32]
            damage=L['DAMAGE_DEFINITION_BASE']+number*L['DAMAGE_DEFINITION_WORDS'];words[damage]=route;words[damage+2]=hits
        domain=dict(first=row,second=second,overrides=overrides)
        entries.append(('definition-view-'+str(index),words,domain));packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    owner,budget,value,route,hits=domain['first'];other_owner,other_budget,other_value,_,_=domain['second'];r1,h1,r2,h2=domain['overrides']
    return [0,owner,budget,value&0xffffffff,value>>32,route,hits,r2,h2,r1,h1,route,hits,owner,other_owner,other_owner,other_budget,other_value&0xffffffff,other_value>>32]


def compare(block,domain):
    expected=native_reference(domain)
    assert list(block[:len(expected)])==expected,(list(block[:len(expected)]),expected)
    assert not any(block[len(expected):]),'Unexpected definition-view probe output'
    return expected
