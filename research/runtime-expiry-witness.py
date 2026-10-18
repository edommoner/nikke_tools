"""One targeted GPU witness for simultaneous expiry, using existing comparators."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('expiry_oracle',ROOT/'scripts/verify-heal-charge.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from verification_session import VerificationSession
_,body,extra=next(c for c in m.d.fixtures() if c[0]=='charge-full-HP')
extra[m.d.N[0]].insert(0,m.d.B('earlier expiring sibling','atk_pct',1,duration=.6))
files=list((ROOT/'app').glob('*.py'))+[ROOT/'app'/n for n in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json','detail_effects.ptx','detail_effects-build.json')]
hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
s=VerificationSession()
try:
    rows=[s.compare(m,'runtime-charge-bulk-expiry',body,extra,backend) for backend in ('native','ptx')]
finally:s.close()
assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
report=dict(passed=all(r['passed'] for r in rows),cases=rows,source_sha256=hashes,scope='Earlier sibling expiry must preserve the charge pool until its own state-end discharge; frame states and full squad checked.')
(ROOT/'research/runtime-expiry-witness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
