"""Shared GPU Geometry cache versus the actual canonical Python dict lifetime."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('cache_core_parent',ROOT/'research/verify-coordinate-core-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_cache_specs import LAYOUT as GC,capacity,check_schema
from portable_coordinate_cache_cases import fixtures,overflow_case
from world_coordinate_geometry_cache_native import capture
SOURCE='gpu/world_coordinate_cache_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross

def compile_case(case):
    from world_frame_native import authored_metadata,roster_names
    from calculator import timeline
    metadata=authored_metadata(case);literal=case.get('literal_weapon_geometry',[dict(spread_start=20.,spread_end=10.,spread_shots=5.) for _ in range(5)])
    for name,wire in zip(roster_names(case),literal):
        weapon=metadata[name];start=float(weapon.get('spread_start',timeline._FALLBACK_SPREAD));end=float(weapon.get('spread_end',start));step=float(weapon.get('spread_change_pershot',0) or 0)
        expected=dict(spread_start=start,spread_end=end,spread_shots=abs(start-end)/step if step else 0.)
        if wire!=expected:raise ValueError('Geometry cache literal spread disagrees with native weapon metadata')
    words,meta,bindings,descriptors=parent.compile_case(case)
    labels=[r['label'] for r in descriptors['rows']]
    if len(labels)!=len(set(labels)):raise ValueError('Geometry cache reference needs unambiguous coordinate labels')
    return words,meta,bindings,descriptors

def prepare():
    check_schema(ROOT);entries,_=parent.prepare()
    for _,_,domain in entries:
        if domain is not None:
            labels=[r['label'] for r in domain[3]['rows']]
            if len(labels)!=len(set(labels)):raise ValueError('Geometry cache reference needs unambiguous coordinate labels')
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case);entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    words,*_=compile_case(overflow_case());entries.append(('reject/coordinate-cache/capacity',words,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    with capture() as observed:result=parent.native_reference(domain)
    observed['final_slots']=[next(r['slot'] for r in domain[3]['rows'] if r['label']==name) for name in observed['final_geometry']['target_names']]
    observed['original_native_sha256']=cross.digest(result)
    return dict(result,geometry_cache=observed)

def compare_cache(block,observed):
    h=GC['BASE'];n=observed['final_target_count'];entries=observed['final_entries'];count=len(entries);stride=12+4*n
    assert list(block[h:h+8])==[GC['MAGIC'],1,1,n,stride,count,capacity(n),observed['geometries']]
    assert block[h+9]==observed['misses'] and block[h+8]+block[h+14]==observed['hits']
    assert block[h+10]==observed['geometries'] and block[h+11]==0 and block[h+12]==observed['peak_entries']
    assert not any(block[h+15:h+GC['HEADER_WORDS']])
    sig=[0]*GC['SIG_WORDS'];sig[0]=n
    fields=observed['final_geometry']['core_bits']+observed['final_geometry']['auto_bits']
    for i,value in enumerate(fields):sig[4+i*2:6+i*2]=[value&0xffffffff,value>>32]
    sig[16:16+n]=observed['final_slots']
    assert list(block[GC['SIG']:GC['TABLE']])==sig,'Geometry cache representative signature'
    table=[0]*GC['SLOTS']
    for i,entry in enumerate(entries):
        words=[]
        for v in entry['key']+entry['value']:words.extend([v&0xffffffff,v>>32])
        at=GC['DATA']+i*stride;assert list(block[at:at+stride])==words,('Geometry cache entry',i)
        hashed=2166136261
        for v in entry['key']:
            hashed=((hashed^(v&0xffffffff))*16777619)&0xffffffff;hashed=((hashed^(v>>32))*16777619)&0xffffffff
        bucket=hashed&(GC['SLOTS']-1)
        while table[bucket]:bucket=(bucket+1)&(GC['SLOTS']-1)
        table[bucket]=i+1
    assert list(block[GC['TABLE']:GC['DATA']])==table,'Geometry cache full-key hash table'
    assert not any(block[GC['DATA']+count*stride:GC['END']]),'Unused cache arena must be zero'

def compare(block,domain):
    with capture() as observed:result=parent.compare(block,domain)
    observed['final_slots']=[next(r['slot'] for r in domain[3]['rows'] if r['label']==name) for name in observed['final_geometry']['target_names']]
    observed['original_native_sha256']=cross.digest(result)
    compare_cache(block,observed)
    return dict(result,geometry_cache=observed)

def validate_rejection(block,name):
    if name=='reject/coordinate-cache/capacity':assert block[0]==64 and block[GC['BASE']+11]==1 and block[GC['BASE']+5]==capacity(127)
    else:parent.validate_rejection(block,name)
