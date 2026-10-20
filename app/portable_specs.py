"""Versioned wire layout for the shared event executor, not effect taxonomy.
Effect/stat/event IDs and force-selection masks come from detail_gpu's compiler.
"""
from pathlib import Path
from portable_trigger_specs import CONDITIONS
from portable_damage_specs import STATS, FLAGS
from world_condition_specs import target_inheritance_events

ABI = 0x50455668
LIMITS = dict(PROTECTION_OBJECTS=1024, PROTECTION_OBJECT_WORDS=24, REMOVALS=4096, LANDINGS=2048, LANDING_WORDS=8, SOURCES=64, SOURCE_SLOTS=32, SOURCE_DEFINITION_WORDS=72, SOURCE_STATE_WORDS=12, RESOURCE_KEYS=256, BATCH=2048, PENDING=512, TRIGGERS=8, CONDITIONS=3, DEFINITIONS=256, CARRIERS=512, LAZY_CACHE=1024, COMMANDS=64, DEPTH=32, TRACE=128, BURST_TRACE=128,
              DEFINITION_WORDS=32, DAMAGE_DEFINITION_WORDS=8, CARRIER_WORDS=23, QUERY_WORDS=32, TRACE_WORDS=8,
              INCOMING_WORDS=4, INCOMING_QUERY_WORDS=20, HEALTH_WORDS=8,
              HEALTH_DEFINITION_WORDS=4, HEALTH_QUERY_WORDS=50,
              DEFINITION_EXTRA_WORDS=8, WEAPON_QUANTITY_WORDS=4,
              WEAPON_MECHANICS_WORDS=28, MODE_TIMING_WORDS=8, WEAPON_STATE_WORDS=16,
              EVENT_WORDS=64, CONDITION_WORDS=12, MODE_WORDS=32,
              WEAPON_WORDS=16, TARGET_WORDS=8, COMBAT_QUERY_WORDS=40,
              COMBAT_STATE_QUERY_WORDS=128)
LIMITS['MASK_WORDS']=(LIMITS['DEFINITIONS']+31)//32


def _place_blocks(start, blocks):
    cursor=start
    for name,size in blocks:
        cursor=(cursor+7)//8*8
        LIMITS[name]=cursor;cursor+=size
    return (cursor+4095)//4096*4096


LIMITS['RECIPIENT_NODES']=256
_n=LIMITS['DEFINITIONS'];_q=LIMITS['COMMANDS'];_m=LIMITS['MASK_WORDS']
LIMITS['INPUT_WORDS']=_place_blocks(32,[
    ('COVER_BASE',5*4),('DEFINITION_BASE',_n*32),('COMMAND_BASE',_q*8),('WEAPON_BASE',5*16),('TARGET_BASE',8*8),
    ('WEAPON_EXTRA_BASE',5*4),('MODE_BASE',_n*32),('EVENT_BASE',_n*64),('CONDITION_BASE',_n*12),
    ('ATTACK_CONTEXT_BASE',5),('WEAPON_MECHANICS_BASE',5*28),('MODE_TIMING_BASE',_n*8),
    ('DEFINITION_EXTRA_BASE',_n*8),('WEAPON_QUANTITY_BASE',5*4),('HEALTH_BASE',5*8),
    ('HEALTH_DEFINITION_BASE',_n*4),('INCOMING_BASE',_q*4),('FORCE_BASE',_n*_m),('RECIPIENT_BASE',_n*8),('BULLET_DEFINITION_BASE',_n*2),('DAMAGE_DEFINITION_BASE',_n*8),('PENDING_EXCLUDE_BASE',_n*_m),('DURATION_DEFINITION_BASE',_n*2),('EVENT_CANDIDATE_BASE',64*_m),('TARGET_ATTACK_BASE',8*2),('AIM_POLICY_BASE',1),('PERIODIC_DEFINITION_BASE',_n*2),('RESOURCE_META_BASE',8),('RESOURCE_DEFINITION_BASE',_n*10),('RESOURCE_CONDITION_BASE',_n*3),('REFERENCE_DEFINITION_BASE',_n*4),('RESOURCE_NAME_BASE',LIMITS['RESOURCE_KEYS']),('SOURCE_DEFINITION_BASE',_n*LIMITS['SOURCE_DEFINITION_WORDS']),('STAGED_DEFINITION_BASE',_n*8),('STAGED_INDEX_BASE',1+_n),('LANDING_META_BASE',8),('STATUS_META_BASE',8),('PROTECTION_META_BASE',8),('PROTECTION_DEFINITION_BASE',_n)])
LIMITS['INPUT_WORDS']=_place_blocks(LIMITS['INPUT_WORDS'],[('RECIPIENT_META_BASE',8),('RECIPIENT_NODE_BASE',LIMITS['RECIPIENT_NODES']*8)])
LIMITS['OUTPUT_WORDS']=_place_blocks(16,[
    ('QUERY_BASE',_q*32),('TRACE_BASE',LIMITS['TRACE']*8),('STATE_BASE',_n*10),
    ('TIMER_TARGET_BASE',_n*2),('BURST_TRACE_BASE',LIMITS['BURST_TRACE']*8),('COMBAT_QUERY_BASE',_q*40),
    ('TARGET_STATE_BASE',8*10),('COMBAT_STATE_QUERY_BASE',_q*128),('COUNTER_STATE_BASE',_n*8),
    ('PERIOD_STATE_BASE',_n*4),('WEAPON_STATE_BASE',5*16),('HEALTH_QUERY_BASE',_q*50),
    ('HEALTH_STATE_BASE',50),('INCOMING_QUERY_BASE',_q*20),('INCOMING_STATE_BASE',20),
    ('TIMER_MASK_BASE',_q*_m),('CARRIER_STATE_BASE',LIMITS['CARRIERS']*LIMITS['CARRIER_WORDS']),('DAMAGE_TRACE_BASE',LIMITS['TRACE']*10),('DAMAGE_ACCOUNTING_QUERY_BASE',_q*40),('DAMAGE_ACCOUNTING_STATE_BASE',56),('COVER_QUERY_BASE',_q*40),('COVER_STATE_BASE',40),('PENDING_QUERY_BASE',_q*4),('PENDING_STATE_BASE',4+LIMITS['PENDING']*8),('PENDING_TRACE_BASE',LIMITS['TRACE']*4),('PERIODIC_STATE_BASE',_n*12),('RESOURCE_STATE_BASE',5*LIMITS['RESOURCE_KEYS']*5),('RESOURCE_QUERY_BASE',_q*12),('RESOURCE_HEADER_BASE',8),('RESOURCE_TRACE_BASE',LIMITS['TRACE']*8),('RESOURCE_STEP_HEAD_BASE',5*LIMITS['RESOURCE_KEYS']),('RESOURCE_STEP_NEXT_BASE',_n*LIMITS['TRIGGERS']),('REFERENCE_CAPTURE_BASE',LIMITS['CARRIERS']*3),('SOURCE_HEADER_BASE',8),('SOURCE_STATE_BASE',LIMITS['SOURCES']*LIMITS['SOURCE_STATE_WORDS']),('SOURCE_LOOKUP_BASE',5*_n),('SOURCE_QUERY_BASE',_q*8),('STAGED_HEADER_BASE',8),('STAGED_STATE_BASE',_n*6),('LANDING_HEADER_BASE',8),('LANDING_STATE_BASE',LIMITS['LANDINGS']*LIMITS['LANDING_WORDS']),('REMOVAL_QUEUE_BASE',LIMITS['REMOVALS']//2),('STACK_NOTICE_VALUE_BASE',LIMITS['REMOVALS']),('IMMUNITY_USED_BASE',13*_n*2),('IMMUNITY_SCRATCH_BASE',_n*4),('PROTECTION_HIT_BASE',_q*5*16),('PROTECTION_QUERY_BASE',_q*50),('PROTECTION_STATE_BASE',50),('PROTECTION_MAP_BASE',LIMITS['CARRIERS']),('PROTECTION_SELECTION_BASE',LIMITS['CARRIERS']),('PROTECTION_OBJECT_BASE',LIMITS['PROTECTION_OBJECTS']*LIMITS['PROTECTION_OBJECT_WORDS']),('PROTECTION_BUILD_BASE',10)])

# Keep every prior output word fixed; append full five-by-five split traces.
LIMITS['OUTPUT_WORDS']=_place_blocks(LIMITS['OUTPUT_WORDS'],[('SPLIT_HIT_BASE',_q*5*4*16),('RECIPIENT_ORDER_BASE',LIMITS['CARRIERS']*2)])

FIELDS = dict(OWNER=0, KIND=1, STAT=2, NAME=3, MAX_STACK=4, BUDGET=5,
              VALUE=6, DURATION=8, INTERVAL=10, IMMEDIATE=12, PRESERVE=13,
              EVENT=14, THRESHOLD=15, COUNT_MODE=16, EVENT_NAME=17,
              TARGET_NAME=18, FORCE_MASK=19, RECIPIENTS=20, TARGET=21, STAGE_ARG=22, STAGE_OVERRIDE=23, REENTRY=24, TOGGLE=25, TRIGGER_COUNT=26, CONDITION_COUNT=27, FLAGS=28, PERIOD=29, DAMAGE_FLAGS=31)


def shader_schema():
    lines = ['// Generated from app/portable_specs.py; do not hand-edit.',
             f'static const uint PORTABLE_ABI = {ABI}U;']
    for prefix, mapping in [('P_', LIMITS), ('D_', FIELDS), ('C_', CONDITIONS), ('S_', STATS), ('H_', FLAGS)]:
        for name,value in mapping.items():
            if prefix=='P_' and name in ('LANDING_WORDS','OUTPUT_WORDS','REMOVAL_QUEUE_BASE','STACK_NOTICE_VALUE_BASE'):
                delta=LIMITS['LANDINGS']*4
                wide=12 if name=='LANDING_WORDS' else value+delta
                lines += ['#ifdef PORTABLE_WIDE_LANDINGS',f'static const uint {prefix}{name} = {wide}U;','#else',f'static const uint {prefix}{name} = {value}U;','#endif']
            else:lines.append(f'static const uint {prefix}{name} = {value}U;')
    events=set(target_inheritance_events())
    # Named hit_count uses compact event 49; shared policy calls it hit_count (8).
    if 8 in events:events.add(49)
    for half in range(2):
        mask=sum(1<<(event%32) for event in events if event//32==half)
        lines.append(f'static const uint P_TARGET_INHERIT_{half} = {mask}U;')
    return '\n'.join(lines)+'\n'


def check_schema():
    path = Path(__file__).resolve().parents[1]/'gpu/portable_schema.slang'
    if path.read_text(encoding='utf-8') != shader_schema():
        raise ValueError('Regenerate gpu/portable_schema.slang from portable_specs.shader_schema()')
