"""Resident coordinate weapon scratch, mutually exclusive with shot groups."""
from pathlib import Path
from portable_coordinate_landing_v1 import INPUT as LANDING_INPUT, OUTPUT as LANDING_OUTPUT

LAYOUT = dict(BASE=900000, INPUT=900000, LANDING=900000+LANDING_INPUT,
              BANK=916000, BANK_WORDS=768, OWNERS=5, TEMPLATE=64,
              PACKET_WORDS=5, PACKET_COUNT=128, INPUT_WORDS=108648,
              OUTPUT_WORDS=1310720)
LAYOUT['END'] = LAYOUT['BANK'] + LAYOUT['BANK_WORDS'] * LAYOUT['OWNERS']
assert LAYOUT['LANDING'] + LANDING_OUTPUT <= LAYOUT['BANK']
assert LAYOUT['TEMPLATE']+LAYOUT['PACKET_WORDS']*LAYOUT['PACKET_COUNT'] <= LAYOUT['BANK_WORDS']
assert 862048 <= LAYOUT['BASE'] < LAYOUT['END'] <= 1048576


def schema():
    return '// Generated resident coordinate weapon scratch.\n'+''.join(
        f'static const uint CF_{key}={value}U;\n' for key, value in LAYOUT.items())


def resident_landing_source(root=None):
    # Only the address space differs: authored shape descriptors and shot
    # values are materialized by the GPU into its owned scratch region.
    # Keep every arithmetic/control-flow byte of the verified integrator.
    root = Path(root or Path(__file__).resolve().parents[1])
    return ('// Generated from coordinate_landing_v1.slang: GPU-owned input only.\n'+
            (root/'gpu/coordinate_landing_v1.slang').read_text().replace('commands[', 'results['))


def check_schema(root=None):
    root = Path(root or Path(__file__).resolve().parents[1])
    assert (root/'gpu/coordinate_physical_layout.slang').read_text() == schema()
    assert (root/'gpu/coordinate_landing_resident_v1.slang').read_text() == resident_landing_source(root)


def audit_arena(root=None):
    from portable_arena_specs import attack_group_layout, coordinate_layout
    ag = attack_group_layout(); cp = coordinate_layout(1048576)
    assert ag['COMPACT'] <= LAYOUT['BASE'] < LAYOUT['END'] <= ag['OUTPUT_WORDS'] <= cp['BASE']
    root = Path(root or Path(__file__).resolve().parents[1])
    source = (root/'gpu/coordinate_physical_runtime.slang').read_text()
    assert 'commands[s.inputBase+104402]!=0' in source, 'Dormant group arena must have no owners'
    assert 'slot*8]==62)return false' in source, 'Group-trigger definitions must be rejected'
    return dict(input_words=LAYOUT['INPUT_WORDS'], output_words=LAYOUT['OUTPUT_WORDS'],
                scratch_begin=LAYOUT['BASE'], scratch_end=LAYOUT['END'],
                requires_disabled_attack_group_owner_mask=True, public_gpu_admitted=False)
