"""Product lowering onto the existing literal ADD attack/self-destruct wire."""
import copy
from dataclasses import replace

from portable_add_attack_battle_wire import LAYOUT as A


def lower(prepared):
    from calculator.boss_pattern import validate
    raw = prepared['enemy'].get('patterns') or []
    if not any(p.get('kind') == 'summon' and p.get('spec', {}).get('attack') for p in raw):
        return prepared, None
    patterns = validate(copy.deepcopy(raw), squad_size=5)
    lowered = copy.deepcopy(prepared)
    lowered['_product_add_attacks'] = True
    if any(p.summon and p.summon.attack and p.summon.attack.debuffs for p in patterns):
        # Original declarations only. The ordinary graph/pool compiler still
        # sees the lowered lifecycle; the shared boss compiler owns effects.
        lowered['_product_add_debuff_patterns'] = copy.deepcopy(raw)
        lowered['_product_boss_debuffs'] = True
    for p, row in zip(patterns, lowered['enemy']['patterns'], strict=True):
        if p.summon is None or p.summon.attack is None:
            continue
        if p.summon.self_destruct and p.summon.attack.hits == 0:
            raise ValueError('Finite self-destruct shot count required')
        for key in ('attack', 'attack_at', 'self_destruct'):
            row['spec'].pop(key, None)
        # Preserve native attack ranking after moving the attack descriptor.
        row['spec']['atk'] = p.summon.atk
    return lowered, patterns


def attach(source, words, metadata, prepared, patterns, authored):
    from portable_actor_specs import compile_registry
    from calculator.boss_pattern import validate
    from portable_add_attack_battle_wire import pack, check_schema
    from portable_add_self_destruct_wire import check_schema as check_retirement
    from portable_world_schedule_specs import number
    from portable_runtime import UnsupportedPortable
    entries = {
        'gpu/product_battle_entry.slang': 104400,
        'gpu/product_group_battle_entry.slang': 104408,
        'gpu/product_fixed_battle_entry.slang': 104400,
        'gpu/product_fixed_group_battle_entry.slang': 104408,
        'gpu/product_target_battle_entry.slang': 110112,
        'gpu/product_fixed_target_battle_entry.slang': 110112,
        'gpu/product_group_target_battle_entry.slang': 104672,
        'gpu/product_fixed_group_target_battle_entry.slang': 104672,
    }
    if source not in entries:
        raise UnsupportedPortable('Product ADD incoming with target modifier carriers is not connected')
    if len(words) != entries[source]:
        raise ValueError('Product ADD prefix stride changed')
    check_schema(); check_retirement()
    _, bindings = compile_registry(validate(copy.deepcopy(prepared['enemy']['patterns'])), pools=True)
    # Reuse the common packer; retirement/delay occupy its declared extension.
    plain = [replace(p, summon=replace(p.summon, self_destruct=False,
                     attack=replace(p.summon.attack, debuffs=()) if p.summon.attack else None))
             if p.summon is not None else p for p in patterns]
    bank = pack(plain, bindings, authored)
    labels = [''] * len(bindings)
    for slot, b in enumerate(bindings):
        if int(b.kind) == 5:
            labels[slot] = f'{patterns[b.run].summon.name}#{b.slot + 1}'
    for p in patterns:
        if p.summon is None or p.summon.attack is None:
            continue
        at = A['ROW_BASE'] + p.idx * A['ROW_WORDS']
        bank[at + 4] = int(p.summon.self_destruct)
        bank[at + 5:at + 7] = number(p.summon.attack_at)
        if p.summon.attack.debuffs:
            from portable_specs import LIMITS as L
            anchor = L['WORLD_FRAME_PAYLOAD_BASE'] + p.idx * 16
            descriptor = words[anchor + 4:anchor + 8]
            if descriptor[0] == 0 or descriptor[1] != len(p.summon.attack.debuffs) or descriptor[2] != 0x42444631:
                raise ValueError('Product ADD debuff definitions were not compiled')
            bank[at + 12:at + 16] = descriptor
            # The common external-definition and bound-lifetime registry uses
            # WF_PAYLOAD. This literal mirror is never a second firing source:
            # WS has zero shots, and GPU admission requires all16 words equal.
            words[anchor:anchor + 16] = bank[at + 8:at + 24]
    words.extend([0] * (A['BASE'] - len(words)))
    words.extend(bank)
    metadata['product_add_attacks'] = dict(
        labels=labels, source_nodes=[b.run for b in bindings],
        input_words=A['INPUT_WORDS'], output_words=A['OUTPUT_WORDS'],
        CPU_schedule_or_state_supplied=False,
        model='original-scheduled-ADD-attacks-and-final-shot-retirement-v1')
    return source.replace('gpu/product_', 'gpu/product_add_', 1), A['INPUT_WORDS'], A['OUTPUT_WORDS'], words, metadata


def query_sources(block, metadata):
    """Read actual slot/generation receipts; labels are literal declarations."""
    from portable_specs import LIMITS as L
    from portable_add_self_destruct_wire import MAGIC as retirement_magic, LAYOUT as R
    from portable_add_attack_battle_wire import MAGIC
    from portable_runtime import UnsupportedPortable
    info = metadata.get('product_add_attacks')
    if info is None:
        return None
    def fail():
        raise UnsupportedPortable('Invalid product ADD source receipt')
    if len(block) != A['OUTPUT_WORDS'] or block[A['OUTPUT_BASE']] != MAGIC or block[R['OUTPUT_BASE']] != retirement_magic:
        fail()
    head = L['WORLD_FRAME_OUTPUT_BASE']; result = {}; shots = 0
    if block[head + 2] > A['MAP_ROWS']:
        fail()
    for i in range(block[head + 2]):
        at = head + 2832 + i * 6
        slot, generation = block[A['OUTPUT_BASE'] + A['MAP_BASE'] + i * 2:A['OUTPUT_BASE'] + A['MAP_BASE'] + i * 2 + 2]
        if block[at] != 3:
            if slot or generation: fail()
            continue
        shots += 1
        if slot >= len(info['labels']) or generation == 0 or (slot != 0 and
                (not info['labels'][slot] or info['source_nodes'][slot] != block[at + 1])):
            fail()
        query = block[at + 5]
        if query == 0 or query - 1 in result: fail()
        result[query - 1] = info['labels'][slot]
    if shots != block[A['OUTPUT_BASE'] + 1] or block[R['OUTPUT_BASE'] + 1] > R['ROWS'] or block[R['OUTPUT_BASE'] + 2] != block[R['OUTPUT_BASE'] + 1]:
        fail()
    return result
