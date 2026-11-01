"""Existing literal movement bank composed after typed and nearby inputs.

An absent declaration has an entirely zero bank and no motion output. It is
not a synthetic zero-velocity model. All populated rows use the original
movement runtime and original duration-carrier definitions.
"""
import copy
from pathlib import Path
from portable_enemy_movement_wire import WORDS,shader_schema as movement_schema,END as OLD_END,OUT as OLD_OUT

BASE=121936
INPUT=BASE+WORDS
OUT=2032000
LOCK_OUT=2558208
OUTPUT=2165136
LOCK_OUTPUT=2691344
END=OUT+OLD_END-OLD_OUT
LOCK_END=LOCK_OUT+OLD_END-OLD_OUT

def shader_schema():
    return ('#ifdef PORTABLE_PRODUCT_TYPED_LOCK\n'+movement_schema(base=BASE,out=LOCK_OUT,output=LOCK_OUTPUT)+
            '#else\n'+movement_schema(base=BASE,out=OUT,output=OUTPUT)+'#endif\n')

def check_schema(root):
    from portable_wire_layout import check_metal
    check_metal(root,OUTPUT);check_metal(root,LOCK_OUTPUT)
    if (Path(root)/'gpu/product_typed_movement_layout.slang').read_text()!=shader_schema():raise ValueError('Typed movement schema drift')
    if not BASE+WORDS==123732 or not OUT<END<=OUTPUT or not LOCK_OUT<LOCK_END<=LOCK_OUTPUT:raise ValueError('Typed movement banks overlap')

def append_bank(words,meta,prepared,bindings,*,logical_base=115680):
    from portable_enemy_movement_wire import movement_bank,lower_effects
    if len(words)!=BASE:raise ValueError('Complete typed/nearby prefix required before movement')
    spec=prepared.get('reference_models',{}).get('enemy_movement')
    if spec is None:words.extend([0]*WORDS);return
    _,tags=lower_effects(prepared)
    words.extend(movement_bank(words,meta,bindings,spec['logical_geometry'],spec['motion'],tags,logical_base=logical_base,allow_empty=True))
    meta['product_typed_movement']=dict(declarations={'enemy_movement':copy.deepcopy(spec)},bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],cpu_state_or_schedule_supplied=False)

def read_result(block,meta,duration,*,locked=False):
    from portable_product_movement import read_result as movement
    base,end,output=(LOCK_OUT,LOCK_END,LOCK_OUTPUT) if locked else (OUT,END,OUTPUT)
    if len(block)!=output or any(block[end:]):raise ValueError('Complete typed movement readback and zero tail required')
    info=meta.get('product_typed_movement')
    if info is None:
        if any(block[base:end]):raise ValueError('Undeclared typed movement output')
        return None
    return movement(block,dict(meta,product_enemy_movement=info),duration,output=output,out=base)
