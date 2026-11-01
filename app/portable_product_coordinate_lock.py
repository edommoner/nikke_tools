"""Disjoint complete coordinate and original Lock On arenas; shared consumers."""
import copy
from pathlib import Path
from portable_runtime import UnsupportedPortable
from portable_logical_geometry_wire import SCRATCH
from portable_product_locks import COVER_SKILL_BASE,COVER_SKILL_END,COVER_FATE_BASE,COVER_HISTORY_END
from portable_lock_typed_layout import OUTPUT as LEGACY_OUTPUT
from portable_packet_fates import HEAD as OLD_FATE_HEAD,FLAGS as OLD_FATE_FLAGS,END as OLD_FATE_END,MAGIC
COORDINATE_OUTPUT=SCRATCH['OUTPUT_WORDS']
LEGACY_BASE=786432
SHIFT=COORDINATE_OUTPUT-LEGACY_BASE
INPUT=115680+5136
FATE_EXTRA=LEGACY_OUTPUT+SHIFT
OUTPUT=FATE_EXTRA+1920
assert OUTPUT==2558208


def shader_schema():
    import portable_original_lock_layout as banks
    from portable_physical_lock_layout import BASE
    text='// Generated from portable_product_coordinate_lock; full old arenas relocated.\n'
    text+=f'#define PL_LAYOUT_OFFSET {262144+SHIFT}U\n#define PL_LAYOUT_OUTPUT {OUTPUT}U\n'
    for key,capacity,width,at in [('PL_PULSE',256,16,banks.PULSES),('LP_TRACE',512,16,banks.PACKETS),('TCS_TRACE',2048,20,banks.QUOTAS),('WF_TRACE',8192,8,banks.FRACTIONS),('WT_TRACE',4096,8,banks.TEAMS)]:
        cap={'PL_PULSE':'PL_PULSE_CAPACITY','LP_TRACE':'LP_DIAGNOSTIC_CAPACITY','TCS_TRACE':'TCS_TRACE_CAPACITY','WF_TRACE':'WF_TRACE_CAPACITY','WT_TRACE':'WT_TRACE_CAPACITY'}[key]
        text+=f'#define {cap} {capacity}U\n#define {key}_AT('+('output' if key=='LP_TRACE' else 's')+',index) (('+('output' if key=='LP_TRACE' else '(s).resourceOutput')+f')+{at+SHIFT}U+(index)*{width}U)\n'
    text+='#define PORTABLE_CUSTOM_PACKET_FATES_LAYOUT\n'
    for name,value in dict(HEAD=OLD_FATE_HEAD+SHIFT,FLAGS=OLD_FATE_FLAGS+SHIFT,CAPACITY=2048,END=OLD_FATE_END+SHIFT,MAGIC=MAGIC).items():text+=f'static const uint PF_{name}={value}U;\n'
    text+=f'#define PF_FLAG_AT(output,index) ((index)<128U ? (output)+{OLD_FATE_FLAGS+SHIFT}U+(index) : (output)+{FATE_EXTRA}U+(index)-128U)\n'
    return text


def check_schema(root):
    from portable_original_lock_layout import END
    from portable_lock_typed_layout import check
    from portable_logical_geometry_wire import check_schema as coordinates
    check(root);coordinates(root)
    if (Path(root)/'gpu/product_coordinate_lock_layout.slang').read_text()!=shader_schema():raise ValueError('Coordinate Lock On shader schema differs')
    if not COORDINATE_OUTPUT==LEGACY_BASE+SHIFT<END+SHIFT<FATE_EXTRA<OUTPUT:raise ValueError('Coordinate/typed/lock/fate regions overlap')
    return dict(input_words=INPUT,output_words=OUTPUT,legacy_shift=SHIFT,typed_attack_capacity=128,skill_history_capacity=2048)


class LockView:
    """Bijective old lock arena relocation plus checked full history pages."""
    def __init__(self,block):self.block=block
    def __len__(self):return 2048912
    def __getitem__(self,key):
        if isinstance(key,slice):
            a,b,step=key.indices(len(self));return [self[i] for i in range(a,b,step)]
        if not 0<=key<len(self):raise IndexError(key)
        if key<LEGACY_BASE:return self.block[key]
        if key<LEGACY_OUTPUT:return self.block[key+SHIFT]
        if key<COVER_SKILL_END:
            from portable_skill_history import BASE
            return self.block[BASE+key-COVER_SKILL_BASE]
        if key<COVER_HISTORY_END:return self.block[FATE_EXTRA+key-COVER_FATE_BASE]
        return 0


def validate_trace_addresses(block):
    """Interior references have one logical-case scope in every GPU batch."""
    count=block[COORDINATE_OUTPUT+1]
    for depth in range(32):
        at=COORDINATE_OUTPUT+153568+depth*544
        pointer,identity=block[at+530],block[at+531]
        if pointer==0:
            if identity:raise UnsupportedPortable('Unpaired typed trace identity')
        elif not 1<=identity<=count or pointer!=COORDINATE_OUTPUT+3568+(identity-1)*1040:
            raise UnsupportedPortable('Typed trace pointer must be relative to its logical result')


def read_result(block,metadata,duration):
    from portable_product_locks import read_result as locks
    if len(block)!=OUTPUT or block[0]!=0:raise UnsupportedPortable('Complete coordinate/Lock On readback required')
    for start,end in ((16,1024),(2832,3568),(136688,153568),(170976,262144)):
        if any(block[COORDINATE_OUTPUT+start:COORDINATE_OUTPUT+end]):
            raise UnsupportedPortable('Nonzero unowned coordinate/Lock On typed bank')
    validate_trace_addresses(block)
    # Every real bank is validated by the original strict reader. The virtual
    # cover suffix is zero only after the coordinate history owner is checked.
    copied=copy.copy(metadata);copied['product_lock_cover']=True
    return locks(LockView(block),copied,duration)
