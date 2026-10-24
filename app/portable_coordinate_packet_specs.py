"""Bounded coordinate packet arena, shared by the two generated backends."""
from pathlib import Path
from portable_coordinate_scene_specs import LAYOUT as C
LAYOUT=dict(BASE=786432,HEADER_WORDS=16,FRAME=786448,FRAME_WORDS=C['SNAPSHOT'],CAST=786448+C['SNAPSHOT'],CASTS=32,SNAPSHOT_WORDS=68,PACKETS=786448+C['SNAPSHOT']+32*68,PACKET_COUNT=2048)
LAYOUT['TRACE']=LAYOUT['PACKETS']+LAYOUT['PACKET_COUNT']*68
LAYOUT.update(TRACE_COUNT=4096,TRACE_WORDS=12)
LAYOUT['SELECTION']=LAYOUT['TRACE']+4096*12
LAYOUT['SELECTION_WORDS']=65536
LAYOUT['END']=LAYOUT['SELECTION']+65536
assert LAYOUT['END']<=1048576

def shader_schema():return '// Generated from portable_coordinate_packet_specs.\n'+''.join(f'static const uint CP_{key}={value};\n' for key,value in LAYOUT.items())
def check_schema(root=None):
    assert (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_packet_layout.slang').read_text()==shader_schema()
