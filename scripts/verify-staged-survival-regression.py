"""Run the established incoming corpus through the staged survival interpreter."""
import argparse, hashlib, importlib.util, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('survival_oracle', ROOT/'scripts/verify-staged-survival.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--long', action='store_true')
    ap.add_argument('--backend', choices=['native', 'ptx'], default='native')
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    files = list(json.loads((ROOT/'research/detail-staged-survival-initial-quick.json').read_text(encoding='utf-8'))['source_sha256'])
    files += ['scripts/verify-staged-survival-regression.py']
    sha = lambda p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    hashes = {p: sha(p) for p in files}
    planned = list(m.v.long_fixtures() if args.long else m.v.fixtures(False))
    rows = []
    device = m.v.v.v.Cuda()
    try:
        for name, body, extra in planned:
            try:
                row = m.compare(device, name, body, extra, args.backend)
            except Exception as error:
                row = dict(name=name, passed=False, error=repr(error))
                print(json.dumps(row, ensure_ascii=True), flush=True)
            rows.append(row)
            if not row['passed']:
                break
    finally:
        device.close()
    assert hashes == {p: sha(p) for p in files}
    passed = len(rows) == len(planned) and all(r['passed'] for r in rows)
    report = dict(generated_at=datetime.now(timezone.utc).isoformat(), passed=passed,
                  objective_complete=False, stage_only=True, abi=m.g.DETAIL_ABI,
                  planned_cases=len(planned), not_run_cases=len(planned)-len(rows),
                  cases=rows, source_sha256=hashes, cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(0 if passed else 1)
