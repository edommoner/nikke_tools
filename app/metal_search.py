"""Metal optimizer stages using the existing paired Slang/Swift transport.

No device failure is swallowed here; server.mjs records the reason and retains
CPU recommendations. The selection's host merge is part of the algorithm,
not a device fallback. Legacy CUDA modules and dispatch stay unchanged.
"""
import heapq
import json
import math
from pathlib import Path
import struct
import sys
import time

from portable_backend import execute
from gpu_selector import select_teams as cpu_select

SELECT_INPUT_WORDS, SELECT_OUTPUT_WORDS = 1612, 480
# Seven public float32 values followed by GPU-owned per-candidate scratch.
COMBAT_INPUT_WORDS, COMBAT_OUTPUT_WORDS = 2146, 565
SELECT_MODEL = 'disjoint-beam-metal-u64-v1'
COMBAT_MODEL = 'combat-prefilter-metal-f32-v1'


def selection_wire(states, masks, scores):
    if not 1 <= len(states) <= 4096 or not 1 <= len(masks) <= 160 or len(scores) != len(masks):
        raise ValueError('Invalid Metal selection dimensions')
    candidates = []
    for mask, score in zip(masks, scores):
        if len(mask) != 8 or any(type(v) is not int or not 0 <= v <= 0xffffffff for v in mask) or not isinstance(score, int) or not 0 <= score <= 2**53//5:
            raise ValueError('Invalid Metal selection candidate')
        candidates.extend([*mask, score & 0xffffffff, score >> 32])
    candidates.extend([0]*((160-len(masks))*10))
    words = [len(states)]
    for used, total, _, last in states:
        if len(used) != 8 or any(type(v) is not int or not 0 <= v <= 0xffffffff for v in used) or not 0 <= total <= 2**53 or not 0 <= last <= 0xffffffff:
            raise ValueError('Invalid Metal selection state')
        words.extend([len(masks), last, *used, total & 0xffffffff, total >> 32, *candidates])
    return struct.pack('<'+'I'*len(words), *words)


def merge_selection(raw, state_count, candidate_count, top):
    if len(raw) != state_count*SELECT_OUTPUT_WORDS*4:
        raise RuntimeError('Invalid Metal selection readback length')
    rows = []
    for parent in range(state_count):
        seen = set()
        previous = None
        for rank in range(160):
            lo, hi, choice = struct.unpack_from('<III', raw, (parent*480+rank*3)*4)
            value = lo | hi << 32
            if not value:
                continue
            key = (-value, choice)
            if choice >= candidate_count or choice in seen or value > 2**53+1 or previous is not None and key < previous:
                raise RuntimeError('Invalid Metal selection sorted result')
            seen.add(choice)
            previous = key
            rows.append((parent*candidate_count+choice, value))
    return heapq.nlargest(top, rows, key=lambda row: (row[1], -row[0]))


class MetalSelection:
    name = 'Metal'

    def expand(self, states, masks, scores, top=None):
        raw, receipt = execute('gpu/optimizer_select.slang', 'optimizerSelect', selection_wire(states, masks, scores), SELECT_INPUT_WORDS, SELECT_OUTPUT_WORDS, 'metal')
        self.name = receipt['transport']['device']
        self.receipt = receipt
        return merge_selection(raw, len(states), len(masks), top if top is not None else len(states)*len(masks))

    def close(self):
        pass


def select_teams(body, device=None):
    if body.get('backend') != 'metal':
        raise ValueError('Explicit Metal selection backend required')
    device = device or MetalSelection()
    # Reuse the canonical validation, beam transitions, expanded and width contract.
    result = cpu_select({**body, 'backend': 'cpu'}, device=device)
    result.update(backend='metal', model=SELECT_MODEL, sort_backend='metal', merge_backend='cpu', device=device.name)
    return result


def combat_wire(models):
    if not 1 <= len(models) <= 2048:
        raise ValueError('GPU combat batch must contain 1..2048 squads')
    raw = bytearray(struct.pack('<I', len(models)))
    for m in models:
        if len(m['chars']) != 220 or len(m['enemy']) != 5 or len(m['effects']) > 160:
            raise ValueError('Invalid GPU combat layout')
        for row in m['effects']:
            if len(row) != 12 or not 0 <= row[0] < 5 or not 0 <= row[2] < 24 or row[4] in (5, 6, 10) and row[5] < 1:
                raise ValueError('Invalid GPU combat effect')
        values = m['chars']+[v for row in m['effects']+[[0]*12]*(160-len(m['effects'])) for v in row]+m['enemy']
        if not all(math.isfinite(v) and abs(v) <= 3.4028234663852886e38 for v in values):
            raise ValueError('Non-finite or out-of-range Metal input')
        raw.extend(struct.pack('<I2145f', len(m['effects']), *values))
    return bytes(raw)


class MetalCombat:
    def run(self, models):
        started = time.perf_counter()
        raw, receipt = execute('gpu/optimizer_combat.slang', 'optimizerCombat', combat_wire(models), COMBAT_INPUT_WORDS, COMBAT_OUTPUT_WORDS, 'metal')
        if len(raw) != len(models)*COMBAT_OUTPUT_WORDS*4:
            raise RuntimeError('Invalid Metal combat readback length')
        scores = []
        for i, m in enumerate(models):
            values = struct.unpack_from('<7f', raw, i*COMBAT_OUTPUT_WORDS*4)
            if not all(math.isfinite(v) and 0 <= v <= 2**53 for v in values) or sum(values[:5]) > 2**53:
                raise RuntimeError('Metal combat produced invalid output')
            scores.append(dict(squad=m['names'], damage=int(sum(values[:5])), members=[int(v) for v in values[:5]], shots=int(values[5]), cycles=int(values[6])))
        return dict(scores=scores, backend='metal', model=COMBAT_MODEL, approximate=True, device=receipt['transport']['device'], kernel_ms=round(receipt['transport'].get('gpu_seconds', 0)*1000, 3), transfer_compute_ms=round((time.perf_counter()-started)*1000, 3), transport=receipt['transport'])


def probe():
    from portable_metal_device import probe as device_probe
    from portable_backend import ROOT
    import os
    import shutil
    result = device_probe(ROOT)
    compiler = Path(os.environ.get('NIKKE_SLANG_ROOT', ROOT/'.tools/slang-2026.20-Darwin-arm64'))/'bin/slangc'
    available = result['passed'] and compiler.is_file() and shutil.which('swift') is not None
    return dict(available=available, backend='metal', device=result.get('device'), verification='per-request', model=COMBAT_MODEL, selection_model=SELECT_MODEL, reason=None if available else result.get('error', result.get('stderr') or 'Metal device or Slang toolchain unavailable'))


def dispatch(body):
    if body['action'] == 'metal_search_probe':
        return probe()
    if body.get('backend') != 'metal':
        raise ValueError('Explicit Metal search backend required')
    if body['action'] == 'select':
        return select_teams(body)
    if body['action'] == 'combat_prefilter':
        from gpu_combat import prefilter
        return prefilter(body, None, MetalCombat())
    raise ValueError('Unknown Metal search action')


if __name__ == '__main__':
    try:
        # Import before stdin, matching the UTF-8 adapter boundary.
        import engine_worker
        print(json.dumps(dispatch(json.load(sys.stdin)), ensure_ascii=True))
    except (Exception, SystemExit) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=True))
        sys.exit(1)
