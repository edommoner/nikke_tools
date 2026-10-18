"""Validate scoped v17 evidence without claiming all-character completion."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def raw(path):
    data = (ROOT / path).read_bytes()
    return data.decode('utf-16') if data.startswith(b'\xff\xfe') else data.decode('utf-8-sig')

def read(path):
    return json.loads(raw(path))

def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def write(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

main = read('research/detail-burst-gauge-verification.json')
api = read('research/detail-burst-gauge-api-verification.json')
ui = read('research/detail-burst-gauge-ui-verification.json')
assert ui['passed'] and ui['burst_gauge_mode'] == 'accumulate'
assert ui['displayed_total'] == sum(ui['displayed_members'])
assert main['passed'] and len(main['cases']) == 56
assert not main['cpu_trace_used_as_gpu_input']
for backend in ('native', 'ptx'):
    cases = [c for c in main['cases'] if c['backend'] == backend]
    assert len(cases) == 28 and all(c['passed'] for c in cases)
for report in (main, api):
    assert report['passed']
    for path, digest in report['source_sha256'].items():
        assert sha(path) == digest, path
for key in ('normal_compare_gpu', 'cpu_verification', 'board_gpu', 'cache_separated',
            'unsupported_cpu_fallback', 'gauge_modes_separate'):
    assert api[key], key
assert api['burst_gauge_mode'] == 'accumulate'
reg = raw('research/detail-burst-gauge-tests.log')
match = re.search(r'Ran (\d+) tests in ([\d.]+)s', reg)
assert match and int(match[1]) == 110 and '\nOK' in reg and 'skipped=' not in reg
node = raw('research/detail-burst-gauge-node-tests.log')
assert 'pass 20' in node and 'fail 0' in node
coverage = read('research/detail-coverage-burst-gauge.json')
audit = read('research/detail-all-effects-audit.json')
assert coverage['supported'] == 110 and audit['accepted_contexts'] == 431
previous = read('research/detail-infinite-checkpoint.json')
upstream = {p: h for p, h in previous['source_sha256'].items() if p.startswith('research/upstream/')}
for path, digest in upstream.items():
    assert sha(path) == digest, path
before = read('research/detail-coverage-infinite.json')
was = {r['character'] for r in before['results'] if r['supported']}
added = [r['character'] for r in coverage['results'] if r['supported'] and r['character'] not in was]
files = set(main['source_sha256']) | set(api['source_sha256']) | {
    'research/detail-burst-gauge-verification.json', 'research/detail-burst-gauge-api-verification.json',
    'research/detail-burst-gauge-tests.log', 'research/detail-burst-gauge-node-tests.log',
    'research/detail-coverage-burst-gauge.json', 'research/detail-all-effects-audit.json',
    'research/detail-burst-gauge-ui-fixture.json', 'research/detail-burst-gauge-ui-verification.json',
    'tests/test_detail_burst_gauge.py',
    'research/detail-burst-gauge-cpu-references.json', 'research/detail-burst-gauge-boundary-references.json'}
now = datetime.now(timezone.utc).isoformat()
cp = dict(generated_at=now, passed=True, objective_complete=False, abi='detail_burst_gauge_v17',
          compiled_characters=110, catalog_characters=203, favorite_contexts_compiled=431,
          favorite_contexts_total=812, compilation_is_not_all_context_parity=True,
          new_characters=added, mechanics_cases=56, cases_per_backend=28,
          python_tests_passed=110, python_test_seconds=float(match[2]), node_tests_passed=20,
          normal_api_total=api['total'], workspace_bytes_per_squad=api['compute']['workspace_bytes'],
          normal_ui_verified=True, normal_ui_total=ui['displayed_total'],
          cpu_trace_used_as_gpu_input=False, current_catalog_verified=False,
          scope='Fixed and actual accumulated burst gauge, charge/camera, weapon changes, skill gains, caster speed conversion and callback ordering. Supported static-enemy squads; not every character, effect, favorite or combination.',
          reports=['research/detail-burst-gauge-verification.json', 'research/detail-burst-gauge-api-verification.json', 'research/detail-burst-gauge-tests.log'],
          source_sha256={**{p: sha(p) for p in sorted(files)}, **upstream})
write('research/detail-burst-gauge-checkpoint.json', cp)
n = read('research/detail-expansion-next.json')
n.update(generated_at=now, objective_complete=False, current_checkpoint_path='research/detail-burst-gauge-checkpoint.json', new_characters=added)
n.pop('current_work', None)
n['checkpoint'].update(compile_coverage=110, previous=107, favorite_contexts_accepted=431,
    coverage_path='research/detail-coverage-burst-gauge.json', workspace_abi=cp['abi'],
    workspace_bytes_per_squad=cp['workspace_bytes_per_squad'], python_tests_passed=110,
    node_tests_passed=20, burst_gauge_cases_total=56, normal_api_burst_gauge_gpu_verified=True,
    normal_api_burst_gauge_total=api['total'], current_catalog_verified=False,
    accepted_catalog_characters=None, accepted_catalog_full_squad_cases=None,
    historical_reports_note='v15 catalog212 is historical; no current v17 catalog-wide parity claim.',
    regression_status='passed: Python110, Node20, gauge56 native/PTX and normal API')
n['layout'].update(cached_stat_keys='0..60', workspace_bytes=cp['workspace_bytes_per_squad'],
    stat60='burst_charge_speed_pct caster original raw/landed energy reference',
    query109='burst amount and published charging flag')
n['next_burst_gauge_reference'].update(cpu_only=False, gpu_implemented=True,
    status='Implemented and verified native/PTX and normal API', report=cp['reports'][0])
n['current_checkpoint'] = {'reports': cp['reports'], 'scope': cp['scope'],
    'remaining': 'All-character and all-special-effect migration remains incomplete'}
write('research/detail-expansion-next.json', n)
print(json.dumps({k: v for k, v in cp.items() if k != 'source_sha256'}, ensure_ascii=True))
