"""Exact binding/init/persistence oracle; no CPU battle or GPU-derived values."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('binding_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=104400,OUTPUT=786432)
VALUES=[(1,17,0x123456789abcdef0),(0xffffffff,0,0xffffffffffffffff),(23,511,0),(0,42,0x100000001)]


def prepare():
    from portable_specs import LIMITS
    if (suite.INPUT,suite.OUTPUT)!=(LIMITS['WORLD_RELOAD_INPUT_WORDS'],LIMITS['WORLD_RELOAD_OUTPUT_WORDS']):raise ValueError('Resident binding wire stride changed')
    entries=[];packed=array.array('I',[len(VALUES)])
    for i,(seed,pending,value) in enumerate(VALUES):
        words=[0]*suite.INPUT;words[:4]=[seed,pending,value&0xffffffff,value>>32]
        entries.append((f'resident-slot-{i}',words,(seed,pending,value)));packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    seed,pending,value=domain
    return dict(initial=[0,0,0],seed=seed,pending=pending,value=value,persistent_seed=seed,scope='Sequential distinct resident slots, poisoned before initialization; not battle/GPU concurrency certification')


def compare(block,domain):
    seed,pending,value=domain
    expected=[0,0,0,seed,pending,value&0xffffffff,value>>32,seed]
    assert list(block[:8])==expected,(list(block[:8]),expected)
    assert not any(block[8:]),'Unexpected binding-probe output words'
    return native_reference(domain)
