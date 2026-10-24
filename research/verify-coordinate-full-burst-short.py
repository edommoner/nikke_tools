"""Coordinate opt-in B3 landings and complete shared receipt relocation."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('coordinate_full_burst_parent',ROOT/'research/verify-coordinate-pending-short.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_coordinate_full_burst_cases import fixtures
SOURCE='gpu/world_coordinate_full_burst_entry.slang'
INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case
native_reference=parent.native_reference;compare=parent.compare


def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case)
        entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    case=fixtures()[0];words,meta,_,_=compile_case(case)
    source=next(i for i,e in enumerate(case['effects']) if e.get('land_in_full_burst'))
    row=meta['binding_source_indices'].index(source)
    from portable_specs import LIMITS as L
    for label,at,value in [('descriptor',L['MODE_BASE']+row*L['MODE_WORDS']+17,0),
            ('pending-kind',L['DAMAGE_DEFINITION_BASE']+row*L['DAMAGE_DEFINITION_WORDS']+6,3),
            ('stage',L['WEAPON_BASE']+3,(words[L['WEAPON_BASE']+3]&~7)|2)]:
        bad=list(words);bad[at]=value;entries.append(('reject/coordinate-full-burst-'+label,bad,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def validate_rejection(block,name):
    if name.startswith('reject/coordinate-full-burst-'):assert block[0]==64
    else:parent.validate_rejection(block,name)
