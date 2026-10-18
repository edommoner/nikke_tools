"""Preserve correct GPU math and the incorrect revival positive-control assertion."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=['research/detail-decoy-healing-authored-native.json','research/detail-decoy-healing-authored-ptx.json','research/detail-decoy-healing-real-native.json','research/detail-decoy-healing-regression-native.json','research/detail-decoy-healing-boundary-verification.json','research/detail-Rei-dead-first-cpu-probe.json','research/detail-decoy-healing-fixture-audit.json']
closure=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert all(sha(p)==h for p,h in r['source_sha256'].items()),path;closure.update(r['source_sha256'])
failed=json.loads((ROOT/reports[2]).read_text(encoding='utf-8'));assert not failed['passed'] and len(failed['cases'])==7
last=failed['cases'][-1];assert [k for k,ok in last['checks'].items() if not ok]==['revival_exercised'];assert all(x['passed'] for x in failed['cases'][:-1])
closure.update(['research/archive-decoy-negative-control-initial.py','research/detail-decoy-healing-authored-native.log','research/detail-decoy-healing-authored-ptx.log','research/detail-decoy-healing-real-native.log','research/detail-decoy-healing-regression-native.log'])
dest=ROOT/'research/ports/v38-before-negative-control-fix';assert not dest.exists()
for p in sorted(closure):
    out=(dest/p).resolve();assert out.is_relative_to(dest.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
(dest/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,stage_only=True,GPU_math_mismatch=False,reason='CPU and GPU matched in all completed cases; dead-first Rei never entered a burst and remained down, so expecting revival in that negative control was incorrect.',files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8');print('Preserved source/report closure before correcting the negative-control name and witness.')
