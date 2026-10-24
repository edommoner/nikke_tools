"""Bounded packet integer reduction ABI; final binary64 rounding happens once."""
from pathlib import Path
from portable_coordinate_physical_specs import LAYOUT as PHYSICAL
LAYOUT=dict(MAGIC=0x50495331,HEADER=8,TERMS=PHYSICAL['PACKET_COUNT'],MAX_MULTIPLIER=1024,OUTPUT=8)
LAYOUT['INPUT']=LAYOUT['HEADER']+LAYOUT['TERMS']*2


def schema():
    return '// Generated packet integer reduction ABI.\n'+''.join(f'static const uint PI_{key}={value}U;\n' for key,value in LAYOUT.items())


def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    assert (root/'gpu/packet_integer_layout.slang').read_text()==schema()
