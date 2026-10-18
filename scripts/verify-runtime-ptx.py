"""Portable-backend witnesses, not a second full native regression run."""
import hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from verification_session import VerificationSession

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

charge=load('runtime_ptx_charge','scripts/verify-heal-charge.py')
extra=load('runtime_ptx_extra','scripts/verify-heal-charge-extra.py')
decoy=load('runtime_ptx_decoy','scripts/verify-decoy-healing.py')
cases=[case for case in charge.fixtures('new') if case[1] in ('raw-charge-healer','raw-charge-Rem-sharing','raw-charge-Marciana-storage')]
cases += [(extra,*case) for case in extra.extra.fixtures(extra.m.d) if case[0]=='charge-extra-release-inside-HP-edge']
cases += [(decoy,*case) for case in decoy.real_fixtures() if case[0] in ('raw-Rei-decoy-heal-owned-growth','raw-Rei-decoy-heal-reordered')]
assert len(cases)==6,len(cases)
files=list((ROOT/'app').glob('*.py'))+[ROOT/'app'/name for name in
    ('detail_effects.cu','detail_effects.ptx','detail_effects-build.json')]
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
started=time.perf_counter();session=VerificationSession();rows=[]
try:
    for oracle,name,body,witness in cases:
        row=session.compare(oracle,name,body,witness,'ptx');rows.append(row)
        if not row['passed']:break
finally:session.close()
assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in hashes}
report={'passed':len(rows)==6 and all(row['passed'] for row in rows),'backend':'ptx','cases':rows,
        'seconds':round(time.perf_counter()-started,3),'source_sha256':hashes,
        'scope':'Portable shield/decoy/storage/sharing/charge and nested HP-edge release witnesses; not every native case repeated.'}
(ROOT/'research/runtime-ptx-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
