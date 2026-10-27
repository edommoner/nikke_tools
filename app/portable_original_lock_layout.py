"""Original 30s histories use owned banks in the existing composed wire."""
from portable_packet_fates import END as BASE
from portable_lock_typed_layout import OUTPUT
PULSE_CAPACITY=256
PACKET_CAPACITY=512
QUOTA_CAPACITY=2048
FRACTION_CAPACITY=8192
TEAM_CAPACITY=4096
PULSES=BASE
PACKETS=PULSES+PULSE_CAPACITY*16
QUOTAS=PACKETS+PACKET_CAPACITY*16
FRACTIONS=QUOTAS+QUOTA_CAPACITY*20
TEAMS=FRACTIONS+FRACTION_CAPACITY*8
END=TEAMS+TEAM_CAPACITY*8
assert END<=OUTPUT and BASE%8==0

def shader_layout():
    return ('// Generated from portable_original_lock_layout.py.\n'
        '#define PL_PULSE_CAPACITY '+str(PULSE_CAPACITY)+'U\n'
        '#define PL_PULSE_AT(s,index) ((s).resourceOutput+'+str(PULSES)+'U+(index)*16U)\n'
        '#define LP_DIAGNOSTIC_CAPACITY '+str(PACKET_CAPACITY)+'U\n'
        '#define LP_TRACE_AT(output,index) ((output)+'+str(PACKETS)+'U+(index)*16U)\n'
        '#define TCS_TRACE_CAPACITY '+str(QUOTA_CAPACITY)+'U\n'
        '#define TCS_TRACE_AT(s,index) ((s).resourceOutput+'+str(QUOTAS)+'U+(index)*20U)\n'
        '#define WF_TRACE_CAPACITY '+str(FRACTION_CAPACITY)+'U\n'
        '#define WF_TRACE_AT(s,index) ((s).resourceOutput+'+str(FRACTIONS)+'U+(index)*8U)\n'
        '#define WT_TRACE_CAPACITY '+str(TEAM_CAPACITY)+'U\n'
        '#define WT_TRACE_AT(s,index) ((s).resourceOutput+'+str(TEAMS)+'U+(index)*8U)\n')

def check(root):
    from pathlib import Path
    if (Path(root)/'gpu/original_lock_composition_layout.slang').read_text()!=shader_layout():raise ValueError('Original lock bank layout differs')

def banks_and_project(block,native):
    if len(block)!=OUTPUT:raise AssertionError('Complete original lock arena required')
    counts=[len(native['lock_pulses']),len(native['lock_packet_trace']),len(native['target_count_shots']),len(native['battle']['fractional_hits']),len(native['battle']['team_hits'])]
    banks=[]
    for start,capacity,width,count in zip((PULSES,PACKETS,QUOTAS,FRACTIONS,TEAMS),(PULSE_CAPACITY,PACKET_CAPACITY,QUOTA_CAPACITY,FRACTION_CAPACITY,TEAM_CAPACITY),(16,16,20,8,8),counts,strict=True):
        if count>capacity:raise AssertionError('Original lock history capacity exceeded')
        banks.append([list(block[start+i*width:start+(i+1)*width]) for i in range(count)])
        if any(block[start+count*width:start+capacity*width]):raise AssertionError('Unexpected original lock history padding')
    if any(block[END:]):raise AssertionError('Unowned original lock tail')
    # Bank records are compared in full by the common comparators. Only the
    # copied legacy projection is zeroed after all new memory was accounted for.
    projected=list(block);projected[BASE:]=[0]*(OUTPUT-BASE)
    from portable_packet_fates import compare_and_project
    return compare_and_project(projected,native),banks[0],banks[1],banks[2],banks[3],banks[4]


def history_budget(native):
    """Fail before a GPU claim if complete native histories exceed their banks."""
    from portable_specs import LIMITS as L
    from portable_projectile_specs import TRACE_COUNT
    from portable_physical_lock_layout import SHOT_CAPACITY
    battle=native['battle'];manual=battle['manual_control']
    rows=[('lock_pulses',len(native['lock_pulses']),PULSE_CAPACITY),
        ('lock_packets',len(native['lock_packet_trace']),PACKET_CAPACITY),
        ('shot_quotas',len(native['target_count_shots']),QUOTA_CAPACITY),
        ('fractional_hits',len(battle['fractional_hits']),FRACTION_CAPACITY),
        ('team_hits',len(battle['team_hits']),TEAM_CAPACITY),
        ('lock_snapshots',len(native['lock_shots']),SHOT_CAPACITY),
        ('skill_history',len(native['skill_trace']),128),
        ('packet_fates',len(native['receipt_fates']),128),
        ('physical_shots',len(battle['projectile_shots']),TRACE_COUNT),
        ('reload_events',len(battle['reload_events']),L['WORLD_RELOAD_TRACE_COUNT']),
        ('control_history',len(manual['notifications'])+len(manual['arbitration']),L['WORLD_CONTROL_TRACE_COUNT']),
        ('spawn_notifications',len(battle['enemy_spawn_notifications']),L['WORLD_SPAWN_TRACE_COUNT']),
        ('typed_attacks',len(native['typed']['attacks']),128)]
    for name,count,capacity in rows:
        if count>capacity:raise ValueError('Complete original '+name+' history exceeds declared capacity: '+str(count)+' > '+str(capacity))
    return [dict(history=name,count=count,capacity=capacity) for name,count,capacity in rows]
