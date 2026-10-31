"""Static burst-control literals. No battle state or predicted times are packed."""
import math
import struct

MAGIC = 0x42435631
WORDS = 176
OWNERS = 5
ROW_WORDS = 24
SEQUENCES = 16
PATTERN_CYCLES = 512
INPUT_BASE = 109792
SOURCE = 'gpu/world_coordinate_burst_control_entry.slang'
STATE_BASE = 1769838


def product_patterns(names, patterns):
    """Compact literal priorities in the existing product weapon stage word.

    Reuse the shared policy producer/selector. Current public character presets
    use every:N and short cycle lists; larger lists fail closed, never truncate.
    No counter, selected owner or predicted time is a CPU input.
    """
    policy=pack(names,patterns=patterns)
    result=[]
    for who,name in enumerate(names):
        at=8+who*ROW_WORDS
        if name not in patterns:kind=value=0
        elif patterns[name] is None:kind,value=3,0
        elif policy[at+4]==1:
            kind,value=1,policy[at+5]
            if value>0x7ffff:raise ValueError('Product every:N exceeds its literal uint19 capacity')
        else:
            if any(policy[at+7:at+22]) or policy[at+6]>>19:
                raise ValueError('Product cycle-list patterns require cycles1..19; larger lists need the explicit policy bank')
            kind,value=2,policy[at+6]
        result.append((kind<<11)|(value<<13))
    return result


def empty():
    return [MAGIC, 1, 0, 0, OWNERS, ROW_WORDS, 16, 0] + [0] * (WORDS - 8)


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 180:
        raise ValueError('Finite burst literal in [0,180] required')
    return list(struct.unpack('<II', struct.pack('<d', value)))


def pack(names, *, delays=None, waits=None, patterns=None, sequence=None):
    """Patterns are resolved runner config values, not catalog labels.

    An empty explicit cycle blocks every missing stage. After the explicit
    sequence runs out, automatic ordering resumes. Empty pattern != absence.
    """
    if len(names) != OWNERS or len(set(names)) != OWNERS or any(type(n) is not str or not n for n in names):
        raise ValueError('Five distinct named owners required')
    delays, waits, patterns = [v if v is not None else {} for v in (delays, waits, patterns)]
    for mapping in (delays, waits, patterns):
        if type(mapping) is not dict or set(mapping) - set(names):
            raise ValueError('Unknown burst owner or invalid mapping')
    if sequence is not None and (type(sequence) is not list or len(sequence) > SEQUENCES):
        raise ValueError('Explicit sequence exceeds bounded capacity')
    out = [MAGIC, 1, 1, len(sequence or []), OWNERS, ROW_WORDS, 16, 0] + [0] * (WORDS - 8)
    for who, name in enumerate(names):
        at = 8 + who * ROW_WORDS
        out[at:at+2] = number(delays.get(name, 0))
        wait = waits.get(name, False)
        if wait is not False and (type(wait) not in (int, float) or not math.isfinite(wait) or not .5 <= wait <= 3):
            raise ValueError('wait_own_cooldown must be false or in [0.5,3]')
        out[at+2:at+4] = number(0 if wait is False else wait)
        pattern = patterns.get(name)
        if pattern is None:
            # Presence (even null) disables automatic B1/B2 truncation upstream.
            out[at+22] = int(name in patterns)
        elif type(pattern) is str and pattern.startswith('every:'):
            tail = pattern[6:]
            if not tail.isascii() or not tail.isdecimal() or not 1 <= int(tail) <= 0xffffffff:
                raise ValueError('Positive uint32 every:N required')
            out[at+4:at+6] = [1, int(tail)]
            out[at+22] = 1
        elif type(pattern) is list:
            out[at+4] = 2
            out[at+22] = 1
            for cycle in pattern:
                if type(cycle) is not int or not 1 <= cycle <= PATTERN_CYCLES:
                    raise ValueError('Explicit pattern cycle outside [1,512]')
                out[at+6+(cycle-1)//32] |= 1 << ((cycle-1) % 32)
        else:
            raise ValueError('Resolved every:N or cycle-list pattern required')
    for cycle, stages in enumerate(sequence or []):
        if type(stages) is not dict or set(stages) - {'1', '2', '3'}:
            raise ValueError('Unknown explicit stage')
        for stage in range(1, 4):
            candidates = stages.get(str(stage), [])
            if type(candidates) is not list or len(candidates) > OWNERS or any(n not in names for n in candidates) or len(set(candidates)) != len(candidates):
                raise ValueError('Unique named candidates required')
            out[128+cycle*3+stage-1] = sum((names.index(n)+1) << (i*3) for i, n in enumerate(candidates))
    return out
