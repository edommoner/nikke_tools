"""Canonical intervals in resource-backed views; all scratch words are checked."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_arc_arena as arena
s=importlib.util.spec_from_file_location('arena_arc_parent',ROOT/'research/verify-coordinate-arcs-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
cross=parent.cross
SOURCE='gpu/coordinate_arc_arena_probe.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=arena.ARC_OUTPUT;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)

def prepare():
    arena.check(ROOT)
    entries,_=parent.prepare()
    for mode in range(1,6):
        words=[0]*INPUT_WORDS;words[:3]=[arena.GUARD_MAGIC,1,mode]
        entries.append(('coordinate-arc-arena/storage-guard-'+str(mode),words,dict(storage_guard=mode)))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def diagnostic_words(mode):
    observed=arena.LAST if mode==1 else 0
    words=[0]*OUTPUT_WORDS
    words[:9]=[0,arena.GUARD_MAGIC,mode,int(mode!=1),arena.SENTINEL&0xffffffff,arena.SENTINEL>>32,observed&0xffffffff,observed>>32,1]
    return words

def native_reference(domain):
    if isinstance(domain,dict):
        mode=domain['storage_guard'];assert 1<=mode<=5
        return dict(storage_guard=mode,error=mode!=1,sentinel=arena.SENTINEL,observed=arena.LAST if mode==1 else 0,count=1)
    return parent.native_reference(domain)

def compare(block,domain):
    if isinstance(domain,dict):
        assert list(block)==diagnostic_words(domain['storage_guard']),'Arc arena storage guard'
        return native_reference(domain)
    assert len(block)==OUTPUT_WORDS
    reference=parent.compare(block[:arena.ARC_PREFIX],domain)
    assert not any(block[arena.ARC_PREFIX:]),'Arc arena scratch not scrubbed'
    return reference

def validate_rejection(block,name):
    assert name.startswith('reject/coordinate-arcs-') and list(block)==[64]+[0]*(OUTPUT_WORDS-1)
