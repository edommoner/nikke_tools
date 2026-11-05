"""All membership words and repeated initialization of the actual shared helper."""
import array, sys, importlib.util
from pathlib import Path
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('quantity_visited_cross', ROOT / 'research/summarize-portable-cross-gpu.py')
cross = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cross)
SOURCE = 'gpu/quantity_visited_probe.slang'
STRICT_WIRE_DIMENSIONS = True
suite = SimpleNamespace(INPUT=516, OUTPUT=1056)

def prepare():
    rows = []
    sequences = [(0, []), (1, [0]*512), (31, list(range(30,-1,-1))),
                 (32, [31,0,31,1]), (33, [32,31,0,32]),
                 (255, list(range(254,-1,-1))), (256, list(range(256))),
                 (256, list(range(255,-1,-1))*2), (256, [255,31,32,63,64,127,128,0]*64)]
    for groups, sequence in sequences:
        words = [len(sequence), groups, 2, 0, *sequence, *([0]*(512-len(sequence)))]
        rows.append((f'quantity-visited/{groups}/{len(rows)}', words, words))
    for label, at, value in [('steps',0,513), ('capacity',1,257), ('rounds',2,0),
                             ('rounds-high',2,3), ('reserved',3,1), ('group',4,256), ('padding',515,1)]:
        words = list(rows[6][1]); words[at] = value
        rows.append(('reject/quantity-visited/'+label, words, None))
    raw = array.array('I', [len(rows)])
    for _, words, _ in rows: raw.extend(words)
    if sys.byteorder != 'little': raw.byteswap()
    return rows, raw.tobytes()

def native_reference(words):
    steps, groups, rounds, reserved = words[:4]
    out = [0]*suite.OUTPUT
    if (steps > 512 or groups > 256 or rounds not in (1,2) or reserved or
        any(g >= groups for g in words[4:4+steps]) or any(words[4+steps:])):
        out[0] = 64
        return out
    out[1:4] = [steps, groups, rounds]
    for round in range(rounds):
        visited = set()
        for i, group in enumerate(words[4:4+steps]):
            out[16+512*round+i] = int(group not in visited)
            visited.add(group)
        out[4+round] = len(visited)
        for group in visited: out[1040+8*round+group//32] |= 1 << (group%32)
    return out

def compare(block, domain):
    expected = native_reference(domain)
    assert list(block) == expected, 'Every membership flag, packed word and reserved output must match'
    return expected

def validate_rejection(block, name):
    assert name.startswith('reject/quantity-visited/')
    assert list(block) == [64]+[0]*(suite.OUTPUT-1), 'Exact bounds rejection and zero remainder required'
