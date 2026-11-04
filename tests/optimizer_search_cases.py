"""Deterministic CPU/Metal shared differential corpus; no device work on import."""
import random
import struct


def selection_cases():
    rng = random.Random(63730)
    yield {'candidates': [], 'teamCount': 1, 'width': 1}
    yield dict(candidates=[dict(squad=list('abcde'),damage=True)],teamCount=1,width=True)
    for count in (1, 5):
        for size in (1, 4, 5, 7, 31, 127, 160):
            for style in ('ties', 'large', 'random'):
                names = [f'n{i:03}' for i in range(256)]
                candidates = []
                for i in range(size):
                    # At size 160 the first 52 rows cover exactly all 256 names.
                    squad = [names[(i*5+j) % 256] for j in range(5)] if style == 'ties' else rng.sample(names, 5)
                    damage = 0 if style == 'ties' else 2**53//5-rng.randrange(5) if style == 'large' else rng.randrange(10**10)
                    candidates.append(dict(squad=squad, damage=damage))
                yield dict(candidates=candidates, teamCount=count, width=rng.choice((1, 7, 73, 256)))
    for i in range(60):
        size = rng.randrange(1, 65)
        names = [str(j) for j in range(rng.choice((5, 25, 64, 256)))]
        yield dict(candidates=[dict(squad=rng.sample(names, 5), damage=rng.randrange(4) if i % 2 else rng.randrange(2**40)) for _ in range(size)], teamCount=1 if i % 3 == 0 else 5, width=rng.choice((1, 2, 13, 64)))
    yield dict(candidates=[dict(squad=[f'{i}:{j}' for j in range(5)], damage=0) for i in range(8)], teamCount=5, width=4096)


def emulate_selection_wire(packed):
    """CPU executor of shader wire, including its 256-lane bitonic network."""
    words = struct.unpack('<'+'I'*(len(packed)//4), packed)
    result = bytearray()
    for parent in range(words[0]):
        at = 1+parent*1612
        nc, last = words[at:at+2]
        total = words[at+10] | words[at+11] << 32
        rows = []
        for i in range(256):
            value = 0
            if i < nc:
                c = at+12+i*10
                valid = (last == 0xffffffff or i > last) and all(not (words[at+2+k] & words[c+k]) for k in range(8))
                if valid:
                    value = total+(words[c+8] | words[c+9] << 32)+1
            rows.append((value, i))
        stage = 2
        while stage <= 256:
            stride = stage//2
            while stride:
                for i in range(256):
                    j = i ^ stride
                    if j > i:
                        better = (rows[i][0], -rows[i][1]) > (rows[j][0], -rows[j][1])
                        if better != ((i & stage) == 0):
                            rows[i], rows[j] = rows[j], rows[i]
                stride //= 2
            stage *= 2
        for value, index in rows[:160]:
            result.extend(struct.pack('<III', value & 0xffffffff, value >> 32, index))
    return bytes(result)
