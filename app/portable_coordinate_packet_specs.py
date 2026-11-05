"""Bounded coordinate packet arena, shared by the two generated backends."""
from pathlib import Path
from portable_arena_specs import coordinate_layout,coordinate_shader_schema
LAYOUT=coordinate_layout()
assert LAYOUT['END']<=1048576

def shader_schema():return coordinate_shader_schema()
def check_schema(root=None):
    assert (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_packet_layout.slang').read_text()==shader_schema()
