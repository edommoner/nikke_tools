"""Portable code-generation controls reuse the 13 independent counter cases."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
spec=importlib.util.spec_from_file_location('indexed_portable_counters',ROOT/'scripts/verify-target-counters-detail.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[Path(__file__).resolve(),ROOT/'tests/test_target_counter_runtime.py',ROOT/'data/engine-effect-overrides.json']
files += [ROOT/'app'/name for name in ('detail_effects.cu','detail_effects.ptx','detail_effects-build.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
device=module.Cuda()
try:rows=module.quantities(device,'ptx')
finally:device.close()
stable=before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=stable and len(rows)==13 and all(r['passed'] for r in rows),cases=rows,source_stable=stable,source_sha256=before,
    scope='13 reused authored quantity/lifecycle controls; raw autonomous 90-second counter matrix runs once on native. Portable dispatch layout and shared ordering have separate controls.')
(ROOT/'research/event-index-counters-ptx.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
