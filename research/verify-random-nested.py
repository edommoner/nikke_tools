"""Recheck nested recipient/health semantics after the v20 target resolver refactor."""
import hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('random_nested',ROOT/'scripts/verify-cleanse-nested.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
d=v.v.v.c.Cuda()
try:rows=v.verify(d,'native')+v.verify(d,'ptx')
finally:d.close()
files=['research/verify-random-nested.py','scripts/verify-cleanse-nested.py','scripts/verify-cleanse-detail.py','scripts/audit-debuff-cleanse.py','app/detail_gpu.py','app/engine_worker.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-build.json','app/detail_effects-sm86.json']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),cpu_trace_used_as_gpu_input=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-random-nested-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
