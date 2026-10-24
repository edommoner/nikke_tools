"""Bounded full-key Geometry cache in the already dormant group arena."""
from pathlib import Path
LAYOUT=dict(BASE=920000,HEADER_WORDS=32,SIG=920032,SIG_WORDS=144,TABLE=920176,SLOTS=8192,DATA=928368,END=1048576,MAX_ENTRIES=4096,MAGIC=0x47434331)
def schema():return '// Generated Geometry cache arena.\n'+''.join(f'static const uint GC_{k}={v}U;\n' for k,v in LAYOUT.items())
def capacity(n):
    if type(n) is not int or not 0<=n<=127:raise ValueError('Geometry target count outside0..127')
    return min(LAYOUT['MAX_ENTRIES'],(LAYOUT['END']-LAYOUT['DATA'])//(12+4*n))
def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);assert (root/'gpu/coordinate_cache_layout.slang').read_text()==schema()
    from portable_coordinate_physical_specs import LAYOUT as cf
    from portable_arena_specs import coordinate_layout
    assert cf['END']<=LAYOUT['BASE']<LAYOUT['DATA']<LAYOUT['END']==coordinate_layout(1048576)['BASE']
    assert LAYOUT['TABLE']+LAYOUT['SLOTS']==LAYOUT['DATA'] and LAYOUT['SIG']+LAYOUT['SIG_WORDS']==LAYOUT['TABLE']
    assert capacity(0)==4096 and capacity(127)==231
