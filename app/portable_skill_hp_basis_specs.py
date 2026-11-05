"""Static HP attack basis descriptor; maximum HP stays runtime-owned."""
from damage_basis_specs import damage_basis

MAGIC = 0x48504231
OFFSET = 20
WORDS = 4

def validate(effect, *, combat, world_frame):
    try:
        basis = damage_basis(effect)
    except OverflowError as error:
        raise ValueError('Invalid HP attack-basis percentage') from error
    if basis.mode and (combat is None or not world_frame):
        raise ValueError('HP skill basis requires the private combat world')
    return basis

def pack(words, index, limits, effect, canonical, number):
    basis = damage_basis(effect)
    if not basis.mode:
        return
    if canonical[1] != 3 or canonical[53] != basis.mode or canonical[54] != basis.hp_pct:
        raise ValueError('Canonical HP skill basis descriptor mismatch')
    packet = limits['DAMAGE_DEFINITION_BASE'] + index * limits['DAMAGE_DEFINITION_WORDS']
    if words[packet + 6] == 1:
        raise ValueError('reference_model_gap: deferred burst damage ignores HP skill basis in pinned native')
    at = limits['MODE_BASE'] + index * limits['MODE_WORDS'] + OFFSET
    if any(words[at:at + WORDS]):
        raise ValueError('HP skill basis descriptor overlaps occupied mode words')
    words[at:at + WORDS] = [MAGIC, basis.mode, *number(basis.hp_pct)]
