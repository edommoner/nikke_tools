"""Original 30s histories use owned banks in the existing composed wire."""
from portable_packet_fates import END as BASE
from portable_lock_typed_layout import OUTPUT
PULSE_CAPACITY=256
PACKET_CAPACITY=512
PULSES=BASE
PACKETS=PULSES+PULSE_CAPACITY*16
END=PACKETS+PACKET_CAPACITY*16
assert END<=OUTPUT and BASE%8==0

def shader_layout():
    return ('// Generated from portable_original_lock_layout.py.\n'
        '#define PL_PULSE_CAPACITY '+str(PULSE_CAPACITY)+'U\n'
        '#define PL_PULSE_AT(s,index) ((s).resourceOutput+'+str(PULSES)+'U+(index)*16U)\n'
        '#define LP_DIAGNOSTIC_CAPACITY '+str(PACKET_CAPACITY)+'U\n'
        '#define LP_TRACE_AT(output,index) ((output)+'+str(PACKETS)+'U+(index)*16U)\n')

def check(root):
    from pathlib import Path
    if (Path(root)/'gpu/original_lock_composition_layout.slang').read_text()!=shader_layout():raise ValueError('Original lock bank layout differs')

def banks_and_project(block,native):
    if len(block)!=OUTPUT:raise AssertionError('Complete original lock arena required')
    counts=[len(native['lock_pulses']),len(native['lock_packet_trace'])]
    banks=[]
    for start,capacity,count in zip((PULSES,PACKETS),(PULSE_CAPACITY,PACKET_CAPACITY),counts,strict=True):
        if count>capacity:raise AssertionError('Original lock history capacity exceeded')
        banks.append([list(block[start+i*16:start+(i+1)*16]) for i in range(count)])
        if any(block[start+count*16:start+capacity*16]):raise AssertionError('Unexpected original lock history padding')
    if any(block[END:]):raise AssertionError('Unowned original lock tail')
    # Bank records are compared in full by the common comparators. Only the
    # copied legacy projection is zeroed after all new memory was accounted for.
    projected=list(block);projected[BASE:]=[0]*(OUTPUT-BASE)
    from portable_packet_fates import compare_and_project
    return compare_and_project(projected,native),banks[0],banks[1]
