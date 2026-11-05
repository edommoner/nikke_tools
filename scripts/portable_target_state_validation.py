"""The same malformed raw predicate descriptors are rejected by both GPUs."""
import copy
import struct
from portable_specs import LIMITS as L


def rejection_programs(cases, compile_case):
    outputs, rows = [], []
    for kind in (16, 17, 6):
        case = next(c for c in cases if c.get('target_state_reference') and
                    c['effects'][-1]['trigger']['condition'][0].startswith(
                        {16:'target_state:',17:'not_target_state:',6:'target_stack_above:'}[kind]))
        original, metadata = compile_case(case)
        at = L['CONDITION_BASE'] + (len(case['effects'])-1)*L['CONDITION_WORDS']
        changes = [('name-limit', {at+1:256}), ('name-negative', {at+1:0xffffffff})]
        values = [('nan', float('nan')), ('infinity', float('inf'))]
        values += [('nonzero',1.)] if kind != 6 else [
            ('negative',-1.), ('fraction',.5), ('large',2147483648.), ('negative-infinity',float('-inf'))]
        for name, value in values:
            lo, hi = struct.unpack('<II',struct.pack('<d',value));changes.append((name, {at+2:lo,at+3:hi}))
        for name, updates in changes:
            words = list(original)
            for pos, value in updates.items():words[pos] = value
            outputs.append((words,copy.deepcopy(metadata)))
            rows.append(dict(name=f'target-state-invalid-{kind}-{name}',status=64))
    return outputs, rows
