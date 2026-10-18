"""Versioned wire layout for the shared event executor, not effect taxonomy.
Effect/stat/event IDs and force-selection masks come from detail_gpu's compiler.
"""
from pathlib import Path

ABI = 0x50455631
LIMITS = dict(DEFINITIONS=32, COMMANDS=64, DEPTH=32, TRACE=128,
              INPUT_WORDS=2048, OUTPUT_WORDS=4096, DEFINITION_BASE=32,
              DEFINITION_WORDS=32, COMMAND_BASE=1056, QUERY_BASE=16,
              QUERY_WORDS=32, TRACE_BASE=2064, TRACE_WORDS=8, STATE_BASE=3088)
FIELDS = dict(OWNER=0, KIND=1, STAT=2, NAME=3, MAX_STACK=4, BUDGET=5,
              VALUE=6, DURATION=8, INTERVAL=10, IMMEDIATE=12, PRESERVE=13,
              EVENT=14, THRESHOLD=15, COUNT_MODE=16, EVENT_NAME=17,
              TARGET_NAME=18, FORCE_MASK=19, RECIPIENTS=20)


def shader_schema():
    lines = ['// Generated from app/portable_specs.py; do not hand-edit.',
             f'static const uint PORTABLE_ABI = {ABI}U;']
    for prefix, mapping in [('P_', LIMITS), ('D_', FIELDS)]:
        lines += [f'static const uint {prefix}{name} = {value}U;' for name, value in mapping.items()]
    return '\n'.join(lines)+'\n'


def check_schema():
    path = Path(__file__).resolve().parents[1]/'gpu/portable_schema.slang'
    if path.read_text(encoding='utf-8') != shader_schema():
        raise ValueError('Regenerate gpu/portable_schema.slang from portable_specs.shader_schema()')
