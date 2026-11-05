"""Literal burst operations after original identity verification; no scheduling."""
import copy

def apply(config,chars,sequence):
    from portable_burst_control_specs import pack,SEQUENCES
    if type(config) is not dict or config.get('burst_sequence') is not None:raise ValueError('Original burst sequence cannot be overwritten')
    if type(sequence) is not list or not 1<=len(sequence)<=SEQUENCES:raise ValueError('Declared burst sequence must contain1..16 cycles')
    names=[c['name'] for c in chars]
    pack(names,sequence=sequence)
    stages={c['name']:str(c.get('burst_stage') or c['_weapon']['burst_stage']) for c in chars}
    for cycle in sequence:
        for stage,candidates in cycle.items():
            if any(stages[n] not in (stage,'A') for n in candidates):raise ValueError('Declared burst candidate lacks the original logical stage')
    result=copy.deepcopy(config);result['burst_sequence']=copy.deepcopy(sequence)
    return result
