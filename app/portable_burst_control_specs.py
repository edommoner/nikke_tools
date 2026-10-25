"""Static burst-control literals. No battle state or predicted times are packed."""
import math
import struct

MAGIC = 0x42435631
WORDS = 176
OWNERS = 5
ROW_WORDS = 24
SEQUENCES = 16
PATTERN_CYCLES = 512


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
