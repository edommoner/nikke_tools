"""CPU-only follow-up on ordered endpoint rounding;current GPU fixture is frozen."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ['app', 'scripts', 'tests']]
from test_target_counter_runtime import manager, NAMES

rows = []
for conditions in [['prob:100', 'prob:99.99999999999999'],
                   ['prob:100', 'prob:99.99999999999999', 'prob:0'],
                   ['prob:99.99999999999999', 'prob:100']]:
    authored = dict(name='endpoint', source='스킬1', type='buff', stat='atk_pct',
                    fixed_value=1, duration=-1, target='self',
                    trigger=dict(timing=['on_attack'], condition=conditions))
    bm = manager([authored]);bm.state['rng_expected'] = True
    effect = bm._effects[0][0]
    events = []
    for i in range(20):
        passed = bm._condition_ok(conditions, NAMES[0], i / 60, effect)
        value = bm.state['rng_acc'][('prob', id(effect), NAMES[0])]
        events.append(dict(event=i + 1, passed=passed, accumulator=value,
                           bits=f'{struct.unpack("<Q", struct.pack("<d", value))[0]:016x}'))
    rows.append(dict(conditions=conditions, events=events))
assert [e['passed'] for e in rows[1]['events']] == [False, True] * 10
assert rows[0]['events'][1]['accumulator'] == 1.0
files = ['research/characterize-probability-endpoints.py', 'tests/test_target_counter_runtime.py',
         'research/upstream/nikke-calc-master/calculator/buff_manager.py']
result = dict(passed=True, cpu_only=True, gpu_execution_performed=False,
              current_frozen_gpu_fixture_changed=False, cases=rows,
              rule='Expected-mode endpoint conditions still add,compare and subtract;rounding may leave1.0,so a later0percent condition can succeed',
              next_validation='Include these boundary chains in the next shared fixture expansion;do not optimize0/100percent into unconditional decisions',
              source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files})
(ROOT / 'research/portable-probability-endpoints-native.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native endpoint rounding and zero-percent residual-state behavior verified;CPU-only follow-up')
