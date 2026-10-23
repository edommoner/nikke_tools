"""Full resident output ownership, including older literal-address banks.

Padding is usable only after every maximum-capacity owner is accounted for.
Diagnostic modes may share storage only with an explicit exclusion guard.
"""
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Bank:
    name: str
    base: int
    words: int

    @property
    def end(self):
        return self.base + self.words


def allocate(limits):
    # Preserve every old pool/trace capacity and the786432-word output stride.
    limits['FOCUS_STATE_BASE'] = limits['WORLD_ACTOR_FIELD_ALL_BASE'] + 128 * 12
    limits['FOCUS_CACHE_COUNT'] = 256
    limits['FOCUS_STATE_WORDS'] = 32 + 256 * 8
    limits['NATIVE_QUERY_COUNT'] = 64
    limits['NATIVE_QUERY_CELL_WORDS'] = 136
    limits['NATIVE_QUERY_BANK_COUNT'] = 32
    limits['NATIVE_QUERY_BANK0_BASE'] = limits['WORLD_ACTOR_NOTICE_BASE'] + 1024 * 3
    limits['NATIVE_QUERY_BANK1_BASE'] = limits['WORLD_SKILL_TRACE_BASE'] + 128 * 48
    limits['NATIVE_QUERY_HEADER_WORDS'] = 32
    limits['NATIVE_QUERY_BASE'] = 785440
    # Logical size: the header and two cell banks are deliberately noncontiguous.
    limits['NATIVE_QUERY_WORDS'] = 32 + 64 * 136
    limits['ORDERED_HISTORY_BASE'] = limits['NATIVE_QUERY_BASE'] + 32
    limits['ORDERED_HISTORY_WORDS'] = 64
    limits['NATIVE_DIAG_BASE'] = limits['REVIVAL_BASE'] + limits['REVIVAL_WORDS']
    limits['NATIVE_DIAG_WORDS'] = 16 + 256 * 16
    for mode in ('normal', 'native-query-diagnostic', 'heal-share-diagnostic'):
        verify(limits, mode=mode)


def banks(limits, mode='normal'):
    from portable_parts_skill_specs import BASE, WORDS
    from portable_heal_share_trace import BASE as trace_base, COUNT, WORDS as trace_words
    l = limits
    rows = [Bank('core-and-world-frame', 0, l['WORLD_FRAME_OUTPUT_WORDS']),
            Bank('actor-pools', l['WORLD_ACTOR_POOL_OUTPUT_BASE'],
                 l['WORLD_ACTOR_NOTICE_BASE'] + 1024 * 3 - l['WORLD_ACTOR_POOL_OUTPUT_BASE']),
            Bank('actor-fields', l['WORLD_ACTOR_FIELDS_BASE'],
                 l['WORLD_ACTOR_FIELD_ALL_BASE'] + 128 * 12 - l['WORLD_ACTOR_FIELDS_BASE']),
            Bank('actor-fields-query-scratch', l['WORLD_ACTOR_FIELDS_OUTPUT_WORDS'] - 16, 16),
            Bank('recipients-counters-skill-trace', l['WORLD_ACTOR_RECIPIENT_BASE'],
                 l['WORLD_SKILL_TRACE_BASE'] + 128 * 48 - l['WORLD_ACTOR_RECIPIENT_BASE']),
            Bank('periodic-control-reload-physical-traces', l['WORLD_PERIODIC_DEFINITION_BASE'],
                 l['SKILL_CRITICAL_STATE_BASE'] - l['WORLD_PERIODIC_DEFINITION_BASE']),
            Bank('critical-lazy-base-copy-revival', l['SKILL_CRITICAL_STATE_BASE'],
                 l['REVIVAL_BASE'] + l['REVIVAL_WORDS'] - l['SKILL_CRITICAL_STATE_BASE']),
            Bank('skill-part-receipts', BASE, WORDS), Bank('interrupt-totals', BASE + WORDS, 10),
            Bank('admission-diagnostic', 786416, 16),
            Bank('focus', l['FOCUS_STATE_BASE'], l['FOCUS_STATE_WORDS']),
            Bank('numeric-query-header', l['NATIVE_QUERY_BASE'], l['NATIVE_QUERY_HEADER_WORDS']),
            Bank('numeric-query-cells0', l['NATIVE_QUERY_BANK0_BASE'], l['NATIVE_QUERY_BANK_COUNT'] * l['NATIVE_QUERY_CELL_WORDS']),
            Bank('numeric-query-cells1', l['NATIVE_QUERY_BANK1_BASE'], l['NATIVE_QUERY_BANK_COUNT'] * l['NATIVE_QUERY_CELL_WORDS']),
            Bank('ordered-history', l['ORDERED_HISTORY_BASE'], l['ORDERED_HISTORY_WORDS'])]
    if mode == 'native-query-diagnostic':
        rows.append(Bank('native-query-diagnostic', l['NATIVE_DIAG_BASE'], l['NATIVE_DIAG_WORDS']))
    elif mode == 'heal-share-diagnostic':
        rows.append(Bank('heal-share-diagnostic', trace_base, 8 + COUNT * trace_words))
    elif mode == 'interrupt-aim-diagnostic':
        rows.append(Bank('interrupt-aim-diagnostic', 785536, 16 + 16 * 32))
    elif mode != 'normal':
        raise ValueError('Unknown or incompatible scratch diagnostic modes')
    return rows


def verify(limits, *, mode='normal'):
    if (limits['NATIVE_QUERY_COUNT'], limits['FOCUS_CACHE_COUNT'], limits['LANDINGS'], limits['LANDING_WORDS']) != (64, 256, 2048, 8):
        raise ValueError('Scratch relocation must preserve the declared capacities')
    if limits['NATIVE_QUERY_CELL_WORDS'] != 136 or limits['NATIVE_QUERY_HEADER_WORDS'] != 32:
        raise ValueError('Scratch cell/header footprint differs from its actual readers')
    if limits['NATIVE_QUERY_WORDS'] != 32 + 64 * 136 or limits['FOCUS_STATE_WORDS'] != 32 + 256 * 8:
        raise ValueError('Scratch logical size differs from its actual readers')
    if limits['ORDERED_HISTORY_WORDS'] != 64 or limits['NATIVE_DIAG_WORDS'] != 16 + 256 * 16:
        raise ValueError('Scratch history/diagnostic footprint differs from its writers')
    rows = sorted(banks(limits, mode), key=lambda b: b.base)
    if limits['NATIVE_QUERY_COUNT'] != 2 * limits['NATIVE_QUERY_BANK_COUNT']:
        raise ValueError('Numeric cache bank capacity differs from its logical capacity')
    for i, row in enumerate(rows):
        if type(row.base) is not int or type(row.words) is not int or row.base < 0 or row.words <= 0 or row.end > limits['WORLD_RELOAD_OUTPUT_WORDS']:
            raise ValueError('Scratch bank outside the resident output: ' + row.name)
        if i and rows[i-1].end > row.base:
            raise ValueError('Scratch bank overlap: ' + rows[i-1].name + ' / ' + row.name)
    return dict(verified=True, scope='Resident output ownership, not numerical or GPU execution proof',
                mode=mode, output_words=limits['WORLD_RELOAD_OUTPUT_WORDS'],
                numeric_cache_capacity=limits['NATIVE_QUERY_COUNT'],
                banks=[dict(asdict(b), end=b.end) for b in rows], gpu_calls=0)


def audit_sources(root, limits, *, sources=None):
    """Tie older literal Slang addresses to the inventory, not just LIMITS."""
    import re
    from pathlib import Path
    from portable_parts_skill_specs import BASE
    sources = sources or {}; root = Path(root)
    for name, symbol, expected in (
        ('gpu/skill_part_receipt.slang', 'SKILL_PART_BASE', BASE),
        ('gpu/world_interrupt_runtime.slang', 'WORLD_INTERRUPT_TOTAL_BASE', BASE + 4096),
        ('gpu/world_interrupt_runtime.slang', 'INTERRUPT_AIM_DIAG_BASE', 785536),
        ('gpu/world_interrupt_runtime.slang', 'INTERRUPT_AIM_DIAG_COUNT', 16)):
        text = sources.get(name, (root/name).read_text())
        match = re.search(r'\b'+symbol+r'\s*=\s*(\d+)\s*;', text)
        if match is None or int(match[1]) != expected:
            raise ValueError('Scratch inventory differs from live shader: ' + symbol)
    name = 'gpu/native_query_diagnostic.slang'
    text = sources.get(name, (root/name).read_text())
    guard = '#if defined(PORTABLE_NATIVE_QUERY_DIAGNOSTIC) && defined(PORTABLE_HEAL_SHARE_DIAGNOSTIC)\n#error '
    if guard not in text:
        raise ValueError('Shared diagnostic storage requires an explicit exclusion guard')
    # Older initializers clear their entire padded envelope once. They must
    # finish before any of the newly assigned padding starts holding live state.
    name = 'gpu/program_phases.slang'
    text = sources.get(name, (root/name).read_text())
    for producer in ('WORLD_POOL_INIT(s,output)', 'WORLD_FIELDS_INIT(s,output)', 'COUNTER_INIT(s,output)'):
        if text.index(producer) >= text.index('initializeFocusState(s);'):
            raise ValueError('Scratch initialization order changed: '+producer)
    focus = sources.get('gpu/focus_aim_runtime.slang', (root/'gpu/focus_aim_runtime.slang').read_text())
    if 'initializeInterruptAimDiagnostics(s);' not in focus or 'initializeInterruptAimDiagnostics(s);' in sources.get('gpu/world_actor_pools.slang', (root/'gpu/world_actor_pools.slang').read_text()):
        raise ValueError('Interrupt diagnostic initialization must follow recipient tail clearing')
    return dict(verified=True, modes=[verify(limits, mode=m) for m in (
        'normal', 'native-query-diagnostic', 'heal-share-diagnostic', 'interrupt-aim-diagnostic')],
        incompatible_modes=['native-query-diagnostic', 'heal-share-diagnostic'], gpu_calls=0)
