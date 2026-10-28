"""Literal source/recipient wire for the declared enemy healing contract.

No health, generation, firing times or simulated damage is serialized. The
legacy logical geometry prefix is retained byte for byte; this distinct input
stride is not accepted by any registered GPU entry yet.
"""
import copy
import struct
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from enemy_healing_model import normalize
from portable_specs import LIMITS as L

MAGIC = 0x45484C31
VERSION = 1
LAYOUT = dict(BASE=115680, HEADER=16, ROWS=32, ROW_WORDS=136,
              ROW_BASE=16, TARGET_BASE=4, TARGETS=127, WORDS=4368)
INPUT_WORDS = LAYOUT['BASE'] + LAYOUT['WORDS']
OUTPUT = dict(OUTPUT_BASE=1867648, OUTPUT_HEADER=16, SEEN_BASE=16,
              RECEIPT_BASE=48, RECEIPTS=1024, RECEIPT_WORDS=32,
              OUTPUT_WORDS=2032000)


def shader_schema():
    return '// Generated from portable_enemy_healing_wire; literal declarations only.\n' + ''.join(
        f'static const uint EHL_{key}={value}U;\n' for key, value in
        dict(MAGIC=MAGIC, VERSION=VERSION, **LAYOUT, INPUT_WORDS=INPUT_WORDS, **OUTPUT).items())


def check_schema(root=None):
    path = Path(root or Path(__file__).resolve().parents[1]) / 'gpu/enemy_healing_layout.slang'
    if path.read_text() != shader_schema():
        raise ValueError('Enemy healing declaration schema drift')


@contextmanager
def compiler_policy():
    """Private packing scope only; default enemy stat admission stays closed."""
    import portable_enemy_specs
    with patch.object(portable_enemy_specs, 'ENEMY_BUFF_STATS',
                      portable_enemy_specs.ENEMY_BUFF_STATS | {'heal_received_pct'}):
        yield


def pack(spec, patterns, bindings):
    rows = normalize(spec)
    if not 1 <= len(patterns) <= 32 or not 1 <= len(bindings) <= 128:
        raise ValueError('Complete bounded source world required')
    if int(bindings[0].kind) != 0:
        raise ValueError('BODY-first actor registry required')
    nodes = {p.id: p for p in patterns}
    actors = {b.label: (slot, b) for slot, b in enumerate(bindings)}
    if len(nodes) != len(patterns) or len(actors) != len(bindings):
        raise ValueError('Unique configured sources and actor labels required')
    words = [0] * LAYOUT['WORDS']
    words[:5] = [MAGIC, VERSION, len(rows), len(patterns), len(bindings)]
    for index, row in enumerate(rows):
        source = nodes.get(row['node'])
        if source is None or source.kind != 'idle':
            raise ValueError('Healing source must be an existing idle node')
        at = LAYOUT['ROW_BASE'] + index * LAYOUT['ROW_WORDS']
        words[at:at+4] = [source.idx, len(row['targets']),
                         *struct.unpack('<II', struct.pack('<d', row['amount']))]
        for target, label in enumerate(row['targets']):
            selected = actors.get(label)
            if selected is None:
                raise ValueError('Healing recipient must exist in the source world')
            slot, binding = selected
            if not 0 < slot < 128 or int(binding.kind) != 5 or binding.source != 2:
                raise ValueError('Healing requires an ADD, never BODY/PART')
            if not 0 <= binding.run < len(patterns):
                raise ValueError('Invalid ADD source run')
            hp = patterns[binding.run].summon
            from portable_geometry_specs import number
            if hp is None or hp.hp is None or number(hp.hp) <= 0 or hp.hit_hp or hp.hit_hp_after:
                raise ValueError('Healing requires finite damage-owned ADD health')
            words[at + LAYOUT['TARGET_BASE'] + target] = slot
    return words


def validate(words, prefix, patterns, bindings, schedule_words):
    if len(words) != LAYOUT['WORDS'] or any(type(v) is not int or not 0 <= v <= 0xffffffff for v in words):
        raise ValueError('Enemy healing requires a complete uint32 declaration bank')
    if len(prefix) != LAYOUT['BASE'] or any(type(v) is not int or not 0 <= v <= 0xffffffff for v in prefix):
        raise ValueError('Complete uint32 logical geometry prefix required')
    count = words[2]
    if words[:2] != [MAGIC, VERSION] or not 1 <= count <= 32:
        raise ValueError('Invalid enemy healing header')
    from portable_world_schedule_specs import INPUT_WORDS as SCHEDULE_WORDS
    graph = L['WORLD_FRAME_INPUT_BASE']
    if len(schedule_words) != SCHEDULE_WORDS or prefix[graph:graph+SCHEDULE_WORDS] != schedule_words:
        raise ValueError('Enemy healing source graph owner bytes differ')
    # Check owner bytes against the existing compiler rather than trusting a
    # detached Python registry or a declaration's own slot identifiers.
    from portable_actor_specs import compile_registry
    from portable_actor_pool_specs import compile_pools
    registry, expected = compile_registry(patterns, pools=True)
    if expected != bindings:
        raise ValueError('Enemy healing registry differs from source world')
    base = L['WORLD_ACTOR_INPUT_BASE']
    if prefix[base:base+len(registry)] != registry:
        raise ValueError('Enemy healing actor owner bytes differ')
    pools = compile_pools(patterns, bindings, fields=True)
    for slot, b in enumerate(bindings):
        if int(b.kind) != 5:
            continue
        at = L['WORLD_ACTOR_POOL_DEF_BASE'] + slot * 12
        expected_at = 8 + slot * 12
        if prefix[at:at+12] != pools[expected_at:expected_at+12]:
            raise ValueError('Enemy healing ADD health owner bytes differ')
    rows = []
    for index in range(count):
        at = LAYOUT['ROW_BASE'] + index * LAYOUT['ROW_WORDS']
        node, n = words[at:at+2]
        if node >= len(patterns) or not 1 <= n <= LAYOUT['TARGETS']:
            raise ValueError('Invalid healing source or target count')
        slots = words[at+4:at+4+n]
        if any(not 0 < slot < len(bindings) for slot in slots):
            raise ValueError('Invalid healing target slot')
        amount = struct.unpack('<d', struct.pack('<II', *words[at+2:at+4]))[0]
        rows.append(dict(node=patterns[node].id, targets=[bindings[s].label for s in slots], amount=amount))
    if words != pack(rows, patterns, bindings):
        raise ValueError('Noncanonical healing declarations or nonzero reserved words')
    return dict(source_nodes=count, actors=len(bindings), target_order_preserved=True,
                health_copied=False, generations_copied=False, clock_copied=False,
                gpu_wire_connected=False, gpu_admitted=False)


def compile_enemy_healing(prepared, geometry, spec):
    from calculator.boss_pattern import validate as validate_patterns
    from portable_logical_geometry_wire import compile_logical_geometry
    check_schema()
    before = copy.deepcopy(prepared)
    with compiler_policy():
        prefix, meta, bindings, scene = compile_logical_geometry(prepared, geometry)
    if prepared != before:
        raise ValueError('Enemy healing lowering mutated original prepared input')
    patterns = validate_patterns(prepared['enemy']['patterns'], coord=True)
    from portable_world_schedule_specs import compile_schedule
    graph, _ = compile_schedule(dict(patterns=prepared['enemy']['patterns'], clock='accumulated',
                                    duration=prepared['policies']['config']['duration']), notice_payload=True)
    bank = pack(spec, patterns, bindings)
    report = validate(bank, prefix, patterns, bindings, graph)
    meta['enemy_healing_declarations'] = dict(report, input_words=INPUT_WORDS,
                                            model='declared-source-node-healing-v1')
    return prefix + bank, meta, bindings, scene
