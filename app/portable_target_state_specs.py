"""Enemy named-state predicates; names are opaque, stack thresholds are integers."""
import copy

TARGET_STATE = 16
NOT_TARGET_STATE = 17
TARGET_STACK = 6


def parse(condition):
    if condition.startswith('target_stack_above:'):
        name, separator, threshold = condition[len('target_stack_above:'):].rpartition(':')
        if not separator or not threshold.isascii() or not threshold.isdigit():
            raise ValueError('Invalid target stack threshold')
        value = int(threshold)
        if not 0 <= value <= 2**31 - 1:
            raise ValueError('Target stack threshold outside supported integer range')
        return TARGET_STACK, name, value
    for prefix, kind in [('target_state:', TARGET_STATE), ('not_target_state:', NOT_TARGET_STATE)]:
        if condition.startswith(prefix):
            return kind, condition[len(prefix):], 0
    return None


def compiler_effect(effect):
    conditions = effect.get('trigger', {}).get('condition', [])
    if not any(c.startswith('target_stack_above:') for c in conditions):
        return effect
    result = copy.deepcopy(effect)
    # The legacy compiler allocates the exact name ID but cannot encode this
    # newer predicate. Only immutable descriptor packing replaces its opcode.
    result['trigger']['condition'] = [
        'target_state:' + parse(c)[1] if c.startswith('target_stack_above:') else c
        for c in conditions]
    return result
