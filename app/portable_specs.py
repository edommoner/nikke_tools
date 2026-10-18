"""Versioned wire layout for the shared event executor, not effect taxonomy.
Effect/stat/event IDs and force-selection masks come from detail_gpu's compiler.
"""
from pathlib import Path
from world_condition_specs import target_inheritance_events

ABI = 0x50455632
LIMITS = dict(DEFINITIONS=32, COMMANDS=64, DEPTH=32, TRACE=128,
              INPUT_WORDS=4096, OUTPUT_WORDS=16384, DEFINITION_BASE=32,
              DEFINITION_WORDS=32, COMMAND_BASE=1056, QUERY_BASE=16,
              QUERY_WORDS=32, TRACE_BASE=2064, TRACE_WORDS=8, STATE_BASE=3088,
              WEAPON_BASE=1600, WEAPON_WORDS=16, TARGET_BASE=1680, TARGET_WORDS=8,
              COMBAT_QUERY_BASE=5500, COMBAT_QUERY_WORDS=40, TARGET_STATE_BASE=8100, TIMER_TARGET_BASE=3500, COMBAT_STATE_QUERY_BASE=8192, COMBAT_STATE_QUERY_WORDS=112)
FIELDS = dict(OWNER=0, KIND=1, STAT=2, NAME=3, MAX_STACK=4, BUDGET=5,
              VALUE=6, DURATION=8, INTERVAL=10, IMMEDIATE=12, PRESERVE=13,
              EVENT=14, THRESHOLD=15, COUNT_MODE=16, EVENT_NAME=17,
              TARGET_NAME=18, FORCE_MASK=19, RECIPIENTS=20, TARGET=21)


def shader_schema():
    lines = ['// Generated from app/portable_specs.py; do not hand-edit.',
             f'static const uint PORTABLE_ABI = {ABI}U;']
    for prefix, mapping in [('P_', LIMITS), ('D_', FIELDS)]:
        lines += [f'static const uint {prefix}{name} = {value}U;' for name, value in mapping.items()]
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
