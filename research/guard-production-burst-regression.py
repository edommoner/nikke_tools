"""Preserve the rejected production candidate and temporarily fail closed."""
import hashlib,json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'research/ports/v34-production-before-burst-wait-fix';assert not dest.exists()
reports=['research/detail-survival-api-verification.json','research/detail-survival-browser-verification.json','research/detail-survival-cpu-compat-verification.json']
files=set(reports)|{'research/detail-survival-normal-tests.log','scripts/verify-normal-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/survival_compat.py','app/engine_compat.py','server.mjs','web/index.html'}
for path in reports:files.update(json.loads((ROOT/path).read_text(encoding='utf-8'))['source_sha256'])
files.update(str(p.relative_to(ROOT)) for p in (ROOT/'tests').glob('test_*.py'))
for p in sorted(files):
    target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
raw=(ROOT/'research/detail-survival-normal-tests.log').read_bytes();s=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig',errors='replace');failures=[]
for line in s.splitlines():
    if line.startswith('{'):
        try:r=json.loads(line)
        except ValueError:continue
        if r.get('passed') is False:failures.append(r)
assert len(failures)==4
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=False,objective_complete=False,interrupted_after_known_failure=True,planned_unittest_tests=87,completed_ok_test_lines=len(re.findall(r'\.\.\. ok$',s,re.M)),skipped=0,failures=failures,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(files)})
(ROOT/'research/detail-normal-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(dest/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,files={p:hashlib.sha256((dest/p).read_bytes()).hexdigest() for p in sorted(files)}),indent=2)+'\n',encoding='utf-8')
path=ROOT/'app/detail_gpu.py';s=path.read_text(encoding='utf-8');needle="   elif kind=='buff' and isinstance(stat,str) and re.fullmatch(r'burst_stage_override:(?:[123A]|reenter[123])',stat):\n"
assert needle in s
s=s.replace(needle,needle+"    raise UnsupportedDetail('Dynamic burst-stage effects temporarily use CPU while the blocked-stage regression is being corrected')\n")
path.write_text(s,encoding='utf-8')
needle="  state=logs[incoming_state_offset]\n"
assert needle in s
s=s.replace(needle,"  if any(hit['down'] for hit in payload['incoming_hits']):raise UnsupportedDetail('Lethal incoming hits temporarily use CPU while dead burst-candidate order is being corrected')\n"+needle)
path.write_text(s,encoding='utf-8')
print('Archived the rejected candidate; dynamic burst-stage effects now fall back to CPU until the corrected kernel is verified.')
