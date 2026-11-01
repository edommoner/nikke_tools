"""Original 30s histories use owned banks in the existing composed wire."""
from portable_packet_fates import END as BASE,FLAGS as FATE_FLAGS
from portable_specs import LIMITS as L
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
    if (Path(root)/'gpu/original_lock_composition_layout.slang').read_text()!=shader_layout()+product_schema():raise ValueError('Original lock bank layout differs')

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

# Product-only continuation banks. Legacy prefixes and private/coordinate wires
# retain their exact layout. Every extra row has a disjoint owned address.
PRODUCT_OUTPUT=2032000
PRODUCT_BANKS={}
_cursor=OUTPUT
for _name,_prefix,_capacity,_width,_base in (
    ('pulses',PULSE_CAPACITY,1024,16,PULSES),
    ('packets',PACKET_CAPACITY,2048,16,PACKETS),
    ('quotas',QUOTA_CAPACITY,8192,20,QUOTAS),
    ('fractions',FRACTION_CAPACITY,16384,8,FRACTIONS),
    ('teams',TEAM_CAPACITY,16384,8,TEAMS),
    ('snapshots',31,128,520,1050120),
    ('shot_times',31,128,2,1068368),
    ('skills',128,2048,48,L['WORLD_SKILL_TRACE_BASE']),
    ('fates',128,2048,1,FATE_FLAGS),
):
    PRODUCT_BANKS[_name]=dict(prefix=_prefix,capacity=_capacity,width=_width,base=_base,extra=_cursor)
    _cursor+=(_capacity-_prefix)*_width
PRODUCT_END=_cursor
assert END<=OUTPUT<PRODUCT_END<=PRODUCT_OUTPUT

def product_address(name,index):
    bank=PRODUCT_BANKS[name]
    if type(index) is not int or not 0<=index<bank['capacity']:raise ValueError('Product Lock On history index outside capacity')
    return bank['base']+index*bank['width'] if index<bank['prefix'] else bank['extra']+(index-bank['prefix'])*bank['width']

def product_schema():
    # Use canonical prefix addresses rather than re-deriving relocated layouts.
    from portable_physical_lock_layout import SNAPSHOTS,SHOT_CAPACITY
    from portable_lock_packet_layout import SHOT_TIMES
    from portable_lock_typed_layout import OFFSET
    if PRODUCT_BANKS['snapshots']['base']!=SNAPSHOTS+OFFSET or PRODUCT_BANKS['shot_times']['base']!=SHOT_TIMES+OFFSET or SHOT_CAPACITY!=31:
        raise ValueError('Product continuation prefix differs from canonical lock layout')
    text='#ifdef PORTABLE_PRODUCT_LONG_LOCK\n#define PL_LAYOUT_OUTPUT '+str(PRODUCT_OUTPUT)+'U\n#define PORTABLE_WORLD_SKILL_HISTORY\n#define WORLD_SKILL_HISTORY_ADMIT(s) (true)\n'
    names={'pulses':('PL_PULSE_CAPACITY','PL_PULSE_AT','s'),'packets':('LP_DIAGNOSTIC_CAPACITY','LP_TRACE_AT','output'),'quotas':('TCS_TRACE_CAPACITY','TCS_TRACE_AT','s'),'fractions':('WF_TRACE_CAPACITY','WF_TRACE_AT','s'),'teams':('WT_TRACE_CAPACITY','WT_TRACE_AT','s'),'snapshots':('PL_SHOT_CAPACITY','PL_SNAPSHOT_AT','s'),'shot_times':(None,'LP_SHOT_TIME_AT','s'),'skills':('WORLD_SKILL_TRACE_CAPACITY','WORLD_SKILL_TRACE_AT','s'),'fates':('PORTABLE_PACKET_FATE_CAPACITY','PF_FLAG_AT','output')}
    for name,bank in PRODUCT_BANKS.items():
        capacity,macro,arg=names[name];base='(output)' if arg=='output' else '(s).resourceOutput'
        if capacity:text+=f'#undef {capacity}\n#define {capacity} {bank["capacity"]}U\n'
        text+=f'#undef {macro}\n#define {macro}({arg},index) ((index)<{bank["prefix"]}U ? {base}+{bank["base"]}U+(index)*{bank["width"]}U : {base}+{bank["extra"]}U+((index)-{bank["prefix"]}U)*{bank["width"]}U)\n'
    return text+'#endif\n'

def product_rows(block,name,count):
    """Read every ordered row and reject unused prefix/continuation words."""
    bank=PRODUCT_BANKS[name];width=bank['width'];start=bank['base']
    if type(count) is not int or not 0<=count<=bank['capacity']:raise ValueError('Product Lock On history count outside capacity')
    if len(block)!=PRODUCT_OUTPUT:raise ValueError('Complete product Lock On arena required')
    prefix=min(count,bank['prefix']);extra=max(0,count-bank['prefix'])
    if any(block[start+prefix*width:start+bank['prefix']*width]) or any(block[bank['extra']+extra*width:bank['extra']+(bank['capacity']-bank['prefix'])*width]):
        raise ValueError('Unexpected product Lock On history padding')
    return [list(block[product_address(name,i):product_address(name,i)+width]) for i in range(count)]
