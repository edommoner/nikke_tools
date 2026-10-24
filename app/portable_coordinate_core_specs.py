"""Authored core node centres only; no lifecycle, winner or probability in IR."""
from pathlib import Path
from portable_coordinate_scene_specs import bits
BASE_INPUT=108648
HEADER=16
NODES=32
NODE_WORDS=4
INPUT=HEADER+NODES*NODE_WORDS
INPUT_WORDS=BASE_INPUT+INPUT
OUTPUT_WORDS=1310720
MAGIC=0x43435231

def schema():
    return '// Generated private live core descriptors.\n'+''.join(f'static const uint CC_{k}={v}U;\n' for k,v in dict(BASE_INPUT=BASE_INPUT,HEADER=HEADER,NODES=NODES,NODE_WORDS=NODE_WORDS,INPUT=INPUT,MAGIC=MAGIC).items())

def check_schema(root=None):
    assert (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_core_layout.slang').read_text()==schema()

def compile_core(case,patterns):
    from calculator.boss_pattern import coord_spec
    if not 1<=len(patterns)<=NODES:raise ValueError('Core nodes require1..32 authored patterns')
    spec=coord_spec(case['enemy'].get('coord'))
    if spec is None:raise ValueError('Core profile requires coordinate mode')
    words=[0]*INPUT;words[:4]=[MAGIC,1,len(patterns),int(spec.auto_aim is None)]
    for p in patterns:
        if p.kind=='core':words[HEADER+p.idx*NODE_WORDS:HEADER+(p.idx+1)*NODE_WORDS]=bits(p.core_at[0])+bits(p.core_at[1])
    return words
