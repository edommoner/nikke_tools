"""Compose existing movement and radial/count consumers on one actor clock."""
import copy
from pathlib import Path
from portable_runtime import UnsupportedPortable
from portable_enemy_movement_wire import INPUT as MOVEMENT_INPUT,OUT as MOVEMENT_OUT,FRAMES,FRAME_WORDS,SEGMENT_WORDS,OUTPUT as ORIGINAL_OUTPUT
from portable_named_range_battle_wire import BASE as RANGE_BASE,WORDS as RANGE_WORDS,OUT as RANGE_OUT,END as RANGE_END
INPUT=MOVEMENT_INPUT+RANGE_WORDS
CAPACITY=8192
OUTPUT=2165136
OUT=MOVEMENT_OUT+FRAMES+CAPACITY*(FRAME_WORDS+SEGMENT_WORDS)
END=OUT+(RANGE_END-RANGE_OUT)

def check_schema(root=None):
    from portable_enemy_movement_wire import check_schema as movement,shader_schema as movement_schema
    from portable_named_range_battle_wire import check_schema as ranges,shader_schema
    root=Path(root or Path(__file__).resolve().parents[1]);movement(root);ranges(root)
    if not RANGE_BASE<MOVEMENT_INPUT<INPUT or not RANGE_OUT<OUT<END<=OUTPUT:
        raise ValueError('Movement/range consumer banks overlap')
    expected=movement_schema(capacity=CAPACITY,output=OUTPUT)+shader_schema(base=MOVEMENT_INPUT,out=OUT,output=OUTPUT)
    if (root/'gpu/product_movement_range_layout.slang').read_text()!=expected:
        raise ValueError('Movement/range composition schema drift')

def compile_product(prepared):
    from portable_enemy_movement_wire import lower_effects,movement_bank
    from portable_product_named_range import compile_product as ranges
    from product_reference_models import normalize
    declarations=normalize(prepared.get('reference_models',{}))
    if set(declarations)!={'enemy_movement','named_range'}:
        raise UnsupportedPortable('Movement/range composition requires both explicit matching coordinate models')
    check_schema();motion=declarations['enemy_movement'];before=copy.deepcopy(prepared)
    lowered,tags=lower_effects(prepared)
    lowered['reference_models']={'named_range':declarations['named_range']}
    source,iw,ow,words,meta=ranges(lowered)
    if iw!=RANGE_BASE+RANGE_WORDS or ow!=ORIGINAL_OUTPUT:raise ValueError('Original range wire changed')
    prefix=words[:RANGE_BASE];bank=words[RANGE_BASE:]
    from portable_actor_specs import compile_registry
    from calculator.boss_pattern import validate
    # Bindings are static identities from the same original actor registry.
    _,bindings=compile_registry(validate(copy.deepcopy(prepared['enemy'].get('patterns') or []),coord=True),pools=True)
    movement=movement_bank(prefix,meta,bindings,motion['logical_geometry'],motion['motion'],tags)
    meta['product_enemy_movement']=dict(declarations={'enemy_movement':motion},bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],cpu_state_or_schedule_supplied=False)
    meta['product_movement_range']=dict(range_output=OUT,range_end=END,input_words=INPUT,output_words=OUTPUT,cpu_state_or_schedule_supplied=False)
    meta['named_range_battle']['input_words']=INPUT
    if prepared!=before:raise ValueError('Original movement/range request was mutated')
    fixed=source=='gpu/product_named_range_fixed_battle_entry.slang'
    return 'gpu/product_movement_range_'+('fixed_' if fixed else '')+'battle_entry.slang',INPUT,OUTPUT,prefix+movement+bank,meta

def read_result(block,metadata,duration):
    from portable_product_movement import read_result as movement
    from portable_product_named_range import read_result as ranges
    check_schema()
    if len(block)!=OUTPUT or any(block[END:]):raise UnsupportedPortable('Incomplete movement/range readback or nonzero unowned tail')
    return [movement(block,metadata,duration,capacity=CAPACITY,output=OUTPUT),ranges(block,metadata,duration,out=OUT,output=OUTPUT)]
