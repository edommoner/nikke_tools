"""Feasibility probe: synthetic builds, no credentials or account access."""
import copy, hashlib, json, os, subprocess, sys, time, zipfile
from pathlib import Path
root = Path(__file__).resolve().parent
archive = root / 'upstream/engine.zip'
with zipfile.ZipFile(archive) as z:
    revision = z.comment.decode('ascii') or None
base = {
    'schema_version': 2,
    'squad': ['리틀 머메이드', '크라운', '라피 : 레드 후드', '헬름', '앨리스'],
    'sim': {'duration': 180, 'expected': True},
    'operation': {'auto': True},
    'profile': {'base': 'default', 'chars': {'크라운': {'skill_levels': [7, 7, 7]}}},
    'profile_level': 'fixed',
}
saved = copy.deepcopy(base)
cases = []
for level in (7, 8, 9, 10, 7):
    case = copy.deepcopy(base)
    case['profile']['chars']['크라운']['skill_levels'] = [7, 7, level]
    cases.append(case)
env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}
started = previous = time.perf_counter()
p = subprocess.Popen([sys.executable, '-m', 'runner.sim', '--batch'],
    cwd=root / 'upstream/nikke-calc-master', stdin=subprocess.PIPE,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', env=env)
p.stdin.write(''.join(json.dumps({**case, 'id': i}, ensure_ascii=False) + '\n'
                     for i, case in enumerate(cases)))
p.stdin.close()
records = []
for line in p.stdout:
    result = json.loads(line)
    if 'error' in result:
        raise RuntimeError(result['error'])
    now = time.perf_counter()
    records.append({'case': result['id'], 'wall_seconds': round(now - previous, 3),
                    'request': cases[result['id']], 'result': result})
    previous = now
    print(f"case {result['id']}: {result['total_damage']} damage, {records[-1]['wall_seconds']} s", flush=True, file=sys.stderr)
err = p.stderr.read()
assert p.wait() == 0, err
assert len(records) == len(cases)
assert records[0]['result']['total_damage'] == records[-1]['result']['total_damage']
assert base == saved
target = records[0]['result']['total_damage'] * 1.01
feasible = [r for r in records[:4] if r['result']['total_damage'] >= target]
report = {
    'purpose': 'engine feasibility; synthetic builds only, not real account predictions',
    'source': 'https://github.com/Jgaram/nikke-calc', 'source_revision': revision,
    'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'python': sys.version,
    'batch_wall_seconds': round(time.perf_counter() - started, 3),
    'checks': {'original_build_unchanged': True, 'repeat_baseline_identical': True},
    'goal_probe': {'target_damage': target, 'rule': 'baseline + 1%; >= target',
        'variable': 'Crown burst level 7..10, other skills fixed at 7',
        'minimum_tested_feasible_level': feasible[0]['request']['profile']['chars']['크라운']['skill_levels'][2] if feasible else None,
        'scope': 'Enumerated single variable; not global optimum; no monotonicity assumption'},
    'records': records,
}
print(json.dumps(report, ensure_ascii=True, indent=2))



