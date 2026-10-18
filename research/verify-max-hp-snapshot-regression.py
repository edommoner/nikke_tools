"""Unique related HP-expiry and typed-storage regression cases, once each."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
hp=load('hp_existing_regression','scripts/verify-survival-scaling.py')
accum=load('accum_existing_regression','scripts/verify-damage-accum.py')
from verification_session import VerificationSession
from gpu_selector import Cuda
files=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]+[ROOT/'app'/name for name in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
selected=[(hp,row) for row in hp.fixtures() if row[0] in ('lost-max-HP-denominator','lost-stacked-HP-gain','lost-scaled-maximum-revival')]
selected += [(accum,row) for row in accum.fixtures() if row[0] in ('raw-damage-accum-combined','raw-damage-accum-owned-reordered')]
assert len(selected)==5
session=VerificationSession();session.device=Cuda();rows=[]
try:
 for module,(name,body,extra) in selected:
  row=session.compare(module,name,body,extra,'native');rows.append(row)
  if not row['passed']:break
finally:session.close()
stable=all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
report=dict(passed=stable and len(rows)==5 and all(row['passed'] for row in rows),cases=rows,source_stable=stable,source_sha256=hashes,scope='Selected existing HP and damage-accumulation interactions only; not a repeated full suite.')
(ROOT/'research/max-hp-snapshot-regression.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
