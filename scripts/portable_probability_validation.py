"""Same malformed probability wire inputs on CUDA and Metal."""
from portable_specs import LIMITS as L


def rejection_programs(cases, compile_case):
    case = next(c for c in cases if c['name'] == 'probability-rate-20-owner-0')
    rows, statuses = [], []
    base = L['CONDITION_BASE']
    mutations = [('name', base + 1, 1), ('negative', base + 3, 0xbfe00000),
                 ('above-one', base + 3, 0x3ff00001), ('nan', base + 3, 0x7ff80000),
                 ('positive-infinity', base + 3, 0x7ff00000), ('negative-infinity', base + 3, 0xfff00000)]
    for name, address, value in mutations:
        words, metadata = compile_case(case)
        words[address] = value
        rows.append((words, metadata))
        statuses.append(dict(name='wire-probability-' + name, status=64))
    return rows, statuses
