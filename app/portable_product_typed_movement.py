"""Existing literal movement bank composed after typed and nearby inputs.

An absent declaration has an entirely zero bank and no motion output. It is
not a synthetic zero-velocity model. All populated rows use the original
movement runtime and original duration-carrier definitions.
"""
import copy
from pathlib import Path
from portable_enemy_movement_wire import WORDS,shader_schema as movement_schema,FRAMES,FRAME_WORDS,SEGMENT_WORDS

BASE=121936
INPUT=BASE+WORDS
OUT=2032000
LOCK_OUT=2558208
CAPACITY=8192
WEAPON_PREFIX_CAPACITY=2048
WEAPON_CAPACITY=4096
WEAPON_WORDS=24
END=OUT+FRAMES+CAPACITY*(FRAME_WORDS+SEGMENT_WORDS)
LOCK_END=LOCK_OUT+FRAMES+CAPACITY*(FRAME_WORDS+SEGMENT_WORDS)
SPILL_WORDS=(WEAPON_CAPACITY-WEAPON_PREFIX_CAPACITY+1)*WEAPON_WORDS
QUOTA_PREFIX_CAPACITY=2048
QUOTA_CAPACITY=4096
QUOTA_WORDS=20
QUOTA_EXTRA=LOCK_END+SPILL_WORDS
QUOTA_END=QUOTA_EXTRA+(QUOTA_CAPACITY-QUOTA_PREFIX_CAPACITY)*QUOTA_WORDS
TEAM_PREFIX_CAPACITY=4096
TEAM_CAPACITY=8192
TEAM_EXTRA=QUOTA_END
TEAM_END=TEAM_EXTRA+(TEAM_CAPACITY-TEAM_PREFIX_CAPACITY)*8
OUTPUT=END+SPILL_WORDS+512
LOCK_OUTPUT=TEAM_END+512

def shader_schema():
    from portable_original_lock_layout import QUOTAS,TEAMS
    from portable_product_coordinate_lock import SHIFT
    return ('#ifdef PORTABLE_PRODUCT_TYPED_LOCK\n'+movement_schema(base=BASE,out=LOCK_OUT,output=LOCK_OUTPUT,capacity=CAPACITY)+
            f'static const uint PTQ_KEEP={QUOTA_CAPACITY}U,PTQ_PREFIX={QUOTA_PREFIX_CAPACITY}U,PTQ_PREFIX_BASE={QUOTAS+SHIFT}U,PTQ_EXTRA={QUOTA_EXTRA}U;\n'+
            f'static const uint PTT_KEEP={TEAM_CAPACITY}U,PTT_PREFIX={TEAM_PREFIX_CAPACITY}U,PTT_PREFIX_BASE={TEAMS+SHIFT}U,PTT_EXTRA={TEAM_EXTRA}U;\n'+
            '#else\n'+movement_schema(base=BASE,out=OUT,output=OUTPUT,capacity=CAPACITY)+'#endif\n'+
            f'static const uint PTW_KEEP={WEAPON_CAPACITY}U,PTW_PREFIX={WEAPON_PREFIX_CAPACITY}U,PTW_EXTRA=EMB_END,PTW_END=EMB_END+{SPILL_WORDS}U;\n')

def check_schema(root):
    from portable_wire_layout import check_output_words
    check_output_words(OUTPUT);check_output_words(LOCK_OUTPUT)
    if (Path(root)/'gpu/product_typed_movement_layout.slang').read_text()!=shader_schema():raise ValueError('Typed movement schema drift')
    if not BASE+WORDS==123732 or not OUT<END<END+SPILL_WORDS<OUTPUT or not LOCK_OUT<LOCK_END<LOCK_END+SPILL_WORDS<LOCK_OUTPUT:raise ValueError('Typed movement banks overlap')

def append_bank(words,meta,prepared,bindings,*,logical_base=115680):
    from portable_enemy_movement_wire import movement_bank,lower_effects
    if len(words)!=BASE:raise ValueError('Complete typed/nearby prefix required before movement')
    spec=prepared.get('reference_models',{}).get('enemy_movement')
    if spec is None:words.extend([0]*WORDS);return
    _,tags=lower_effects(prepared)
    words.extend(movement_bank(words,meta,bindings,spec['logical_geometry'],spec['motion'],tags,logical_base=logical_base,allow_empty=True))
    meta['product_typed_movement']=dict(declarations={'enemy_movement':copy.deepcopy(spec)},bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],cpu_state_or_schedule_supplied=False)

def weapon_rows(block,base,count,spill_base):
    """Complete ordered physical history; unused prefix/spill/overflow stay zero."""
    if type(count) is not int or not 0<=count<=WEAPON_CAPACITY:raise ValueError('Typed physical history capacity exceeded')
    head=base+170976
    layout=(2032000,LOCK_END,LOCK_OUTPUT) if spill_base==LOCK_END else (1769856,END,OUTPUT)
    if ((base,spill_base,len(block))!=layout
        or any(block[head+64+min(count,WEAPON_PREFIX_CAPACITY)*WEAPON_WORDS:base+220224])
        or any(block[spill_base+max(count-WEAPON_PREFIX_CAPACITY,0)*WEAPON_WORDS:spill_base+SPILL_WORDS])):
        raise ValueError('Incomplete or nonzero unused typed physical history')
    rows=[]
    for i in range(count):
        at=head+64+i*WEAPON_WORDS if i<WEAPON_PREFIX_CAPACITY else spill_base+(i-WEAPON_PREFIX_CAPACITY)*WEAPON_WORDS
        rows.append(list(block[at:at+WEAPON_WORDS]))
    return rows

def quota_rows(block,count):
    """Original before/after named-capacity receipts across both owned banks."""
    from portable_original_lock_layout import QUOTAS
    from portable_product_coordinate_lock import SHIFT
    start=QUOTAS+SHIFT
    if (len(block)!=LOCK_OUTPUT or type(count) is not int or not 0<=count<=QUOTA_CAPACITY
        or any(block[start+min(count,QUOTA_PREFIX_CAPACITY)*QUOTA_WORDS:start+QUOTA_PREFIX_CAPACITY*QUOTA_WORDS])
        or any(block[QUOTA_EXTRA+max(count-QUOTA_PREFIX_CAPACITY,0)*QUOTA_WORDS:QUOTA_END])):
        raise ValueError('Incomplete typed Lock On shot quota history')
    return [list(block[(start+i*QUOTA_WORDS if i<QUOTA_PREFIX_CAPACITY else QUOTA_EXTRA+(i-QUOTA_PREFIX_CAPACITY)*QUOTA_WORDS):
                       (start+(i+1)*QUOTA_WORDS if i<QUOTA_PREFIX_CAPACITY else QUOTA_EXTRA+(i-QUOTA_PREFIX_CAPACITY+1)*QUOTA_WORDS)]) for i in range(count)]

def team_rows(block,count):
    from portable_original_lock_layout import TEAMS
    from portable_product_coordinate_lock import SHIFT
    start=TEAMS+SHIFT
    if (len(block)!=LOCK_OUTPUT or type(count) is not int or not 0<=count<=TEAM_CAPACITY
        or any(block[start+min(count,TEAM_PREFIX_CAPACITY)*8:start+TEAM_PREFIX_CAPACITY*8])
        or any(block[TEAM_EXTRA+max(count-TEAM_PREFIX_CAPACITY,0)*8:TEAM_END])):
        raise ValueError('Incomplete typed Lock On team event history')
    return [list(block[(start+i*8 if i<TEAM_PREFIX_CAPACITY else TEAM_EXTRA+(i-TEAM_PREFIX_CAPACITY)*8):
                       (start+(i+1)*8 if i<TEAM_PREFIX_CAPACITY else TEAM_EXTRA+(i-TEAM_PREFIX_CAPACITY+1)*8)]) for i in range(count)]

def read_result(block,meta,duration,*,locked=False):
    from portable_product_movement import read_result as movement
    base,end,output=(LOCK_OUT,LOCK_END,LOCK_OUTPUT) if locked else (OUT,END,OUTPUT)
    tail=TEAM_END if locked else end+SPILL_WORDS
    if len(block)!=output or any(block[tail:]):raise ValueError('Complete typed movement readback and zero tail required')
    info=meta.get('product_typed_movement')
    if info is None:
        if any(block[base:end]):raise ValueError('Undeclared typed movement output')
        return None
    return movement(block,dict(meta,product_enemy_movement=info),duration,capacity=CAPACITY,output=output,out=base)
