"""Literal counter input contract for the pending private world adapter.

This module does not admit counters to compile_program or execute a battle.
Policy validation belongs to target_counter_specs; impact validation belongs to
impact_specs. Progress, UID/epoch, readiness and callbacks are GPU outputs.
"""
import math
import struct

from impact_specs import ActorHandle, Impact
from target_counter_specs import specification

MAGIC = 0x57433031  # WC01, independent of the public executor ABI.
VERSION = 1
DEFINITIONS = 256
COMMANDS = 64
POLICY_WORDS = 16
ACTION_WORDS = 16
HEADER_WORDS = 8
POLICY_BASE = HEADER_WORDS
ACTION_BASE = POLICY_BASE + DEFINITIONS * POLICY_WORDS
INPUT_WORDS = ACTION_BASE + COMMANDS * ACTION_WORDS
ACTIVATE, REFRESH, IMPACT, DEATH = 1, 2, 3, 4


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Counter input requires finite binary64')
    return list(struct.unpack('<II', struct.pack('<d', value)))


def _index(value, limit, label):
    if type(value) is not int or not 0 <= value < limit:
        raise ValueError('Invalid counter ' + label)
    return value


def _squad(names):
    if len(names) != 5 or any(not isinstance(n, str) or not n for n in names) or len(set(names)) != 5:
        raise ValueError('Counter input requires five distinct squad names')


def policy_words(effect, owner, name):
    spec = specification(effect)
    if spec is None:
        return [0] * POLICY_WORDS
    # The marker belongs to the enemy sentinel; its explicit Actor is unrelated
    # to that recipient. Other selectors need their own native binding proof.
    if effect.get('target', 'self') not in ('target', 'boss'):
        raise ValueError('Private counter carrier must use the enemy sentinel')
    _index(owner, 5, 'owner'); _index(name, 256, 'name')
    flags = int(spec.preserve) | int(spec.on_death) << 1 | int(spec.owner_only) << 2 | int(spec.single_body) << 3
    return [1, int(spec.actor.kind), spec.actor.identity, spec.actor.generation,
            *_number(spec.threshold), spec.families, spec.outcomes, flags,
            owner, name, *_number(effect.get('duration', -1)), 0, 0, 0]


def action_words(time, action, names):
    """Encode authored stimuli, never CPU state or a simulated hit replay."""
    _squad(names)
    if type(time) not in (int, float) or not math.isfinite(time) or not 0 <= time <= 180:
        raise ValueError('Invalid counter action time')
    if not isinstance(action, (list, tuple)) or not action:
        raise ValueError('Invalid counter action')
    kind, *args = action
    row = [0, *_number(time)] + [0] * 13
    if kind in ('activate', 'refresh') and not args:
        row[0] = ACTIVATE if kind == 'activate' else REFRESH
    elif kind == 'death' and len(args) == 3:
        actor = ActorHandle(*args)
        row[0] = DEATH
        row[4:7] = [int(actor.kind), actor.identity, actor.generation]
    elif kind == 'hit' and len(args) in (7, 8):
        family, outcome, actor_kind, identity, generation, credit, damage, *owner = args
        who = _index(owner[0] if owner else 2, 5, 'attacker')
        packet = Impact(names[who], ActorHandle(actor_kind, identity, generation), family, outcome, damage, credit)
        row[0] = IMPACT
        row[3:14] = [who, int(packet.target.kind), packet.target.identity, packet.target.generation,
                     int(packet.family), int(packet.outcome), *_number(packet.damage), *_number(packet.credit), packet.attack_id]
    else:
        raise ValueError('Unported counter action')
    return row


def pack(effects, actions, names, state_names, *, allow_no_counter=False):
    """Return a fixed sidecar; definition indexes match the common compiler.

    effects contains (authored effect, owner index), not active carriers. Name
    IDs come from the common compiler's immutable symbol table. Child event
    execution and runtime quantities are deliberately absent from this input.
    """
    _squad(names)
    if type(allow_no_counter) is not bool:
        raise ValueError('Explicit boolean required for counter-free world inputs')
    if not 0 < len(effects) <= DEFINITIONS or not 0 < len(actions) <= COMMANDS:
        raise ValueError('Counter input capacity exceeded')
    if not isinstance(state_names, dict) or len(state_names) > 256 or any(not isinstance(n, str) or type(i) is not int or not 0 <= i < 256 for n, i in state_names.items()) or len(set(state_names.values())) != len(state_names):
        raise ValueError('Invalid common compiler name symbols')
    definitions = {}
    words = [0] * INPUT_WORDS
    words[:HEADER_WORDS] = [MAGIC, VERSION, len(effects), len(actions), POLICY_WORDS, ACTION_WORDS, 0, 0]
    for i, (effect, owner) in enumerate(effects):
        _index(owner, 5, 'owner')
        spec = specification(effect)
        if spec is None:
            continue
        key = (owner, effect['name'])
        if key in definitions and definitions[key] != spec:
            raise ValueError('Same named counter requires identical actor and credit policies')
        definitions[key] = spec
        if effect['name'] not in state_names:
            raise ValueError('Counter name missing from common compiler symbols')
        at = POLICY_BASE + i * POLICY_WORDS
        words[at:at + POLICY_WORDS] = policy_words(effect, owner, state_names[effect['name']])
    if not definitions and not allow_no_counter:
        raise ValueError('Counter sidecar requires a counter definition')
    for effect, owner in effects:
        if effect.get('stat') in ('buff_stack_add', 'buff_stack_remove', 'buff_stack_init', 'buff_max_stack_add', 'debuff_stack_add', 'debuff_stack_remove') and (owner, effect.get('target_effect')) in definitions:
            raise ValueError('Counter progress is separate from named buff stack manipulation')
    previous = -1
    for i, (time, action) in enumerate(actions):
        row = action_words(time, action, names)
        if time < previous:
            raise ValueError('Counter actions must be chronological')
        previous = time
        at = ACTION_BASE + i * ACTION_WORDS
        words[at:at + ACTION_WORDS] = row
    return words


def pack_battle(effects, command_count, names, state_names, bindings, patterns, *, allow_no_counter=False):
    """Physical-world sidecar: authored policies and static part reach.

    Mode1 is rejected by the existing literal-only GPU entry. This encoder
    cannot enable that entry or the public application adapter.
    """
    if type(command_count) is not int or not 1 <= command_count <= COMMANDS:
        raise ValueError('Invalid world counter command count')
    for effect, owner in effects:
        if specification(effect) is not None and effect.get('target') != 'boss':
            raise ValueError('World counter carrier must explicitly bind the boss sentinel')
    words = pack(effects, [(0, ('activate',))] * command_count, names, state_names, allow_no_counter=allow_no_counter)
    words[6] = 1
    words[ACTION_BASE:] = [0] * (COMMANDS * ACTION_WORDS)
    if not 1 <= len(bindings) <= 128:
        raise ValueError('Invalid world counter Actor binding count')
    for slot, binding in enumerate(bindings):
        if int(binding.kind) not in (1,6):
            continue
        reach = patterns[binding.run].targets[binding.slot].reach
        if type(reach) is not int or not 0 <= reach <= (5 if int(binding.kind)==1 else 4):
            raise ValueError('Invalid physical part reach')
        at = ACTION_BASE + slot * 8
        words[at:at + 2] = [1 if int(binding.kind)==1 else 2, reach]
    return words
