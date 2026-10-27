"""Original 30s histories use owned banks in the existing composed wire."""
from portable_packet_fates import END as BASE
from portable_lock_typed_layout import OUTPUT
PULSE_CAPACITY=256
PACKET_CAPACITY=512
QUOTA_CAPACITY=2048
PULSES=BASE
PACKETS=PULSES+PULSE_CAPACITY*16
QUOTAS=PACKETS+PACKET_CAPACITY*16
END=QUOTAS+QUOTA_CAPACITY*20
assert END<=OUTPUT and BASE%8==0

def shader_layout():
    return ('// Generated from portable_original_lock_layout.py.\n'
        '#define PL_PULSE_CAPACITY '+str(PULSE_CAPACITY)+'U\n'
        '#define PL_PULSE_AT(s,index) ((s).resourceOutput+'+str(PULSES)+'U+(index)*16U)\n'
        '#define LP_DIAGNOSTIC_CAPACITY '+str(PACKET_CAPACITY)+'U\n'
        '#define LP_TRACE_AT(output,index) ((output)+'+str(PACKETS)+'U+(index)*16U)\n'
        '#define TCS_TRACE_CAPACITY '+str(QUOTA_CAPACITY)+'U\n'
        '#define TCS_TRACE_AT(s,index) ((s).resourceOutput+'+str(QUOTAS)+'U+(index)*20U)\n')

def check(root):
    from pathlib import Path
    if (Path(root)/'gpu/original_lock_composition_layout.slang').read_text()!=shader_layout():raise ValueError('Original lock bank layout differs')

def banks_and_project(block,native):
    if len(block)!=OUTPUT:raise AssertionError('Complete original lock arena required')
    counts=[len(native['lock_pulses']),len(native['lock_packet_trace']),len(native['target_count_shots'])]
    banks=[]
    for start,capacity,width,count in zip((PULSES,PACKETS,QUOTAS),(PULSE_CAPACITY,PACKET_CAPACITY,QUOTA_CAPACITY),(16,16,20),counts,strict=True):
        if count>capacity:raise AssertionError('Original lock history capacity exceeded')
        banks.append([list(block[start+i*width:start+(i+1)*width]) for i in range(count)])
        if any(block[start+count*width:start+capacity*width]):raise AssertionError('Unexpected original lock history padding')
    if any(block[END:]):raise AssertionError('Unowned original lock tail')
    # Bank records are compared in full by the common comparators. Only the
    # copied legacy projection is zeroed after all new memory was accounted for.
    projected=list(block);projected[BASE:]=[0]*(OUTPUT-BASE)
    from portable_packet_fates import compare_and_project
    return compare_and_project(projected,native),banks[0],banks[1],banks[2]
