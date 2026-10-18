"""CPU/compile preflight for additional reserve interactions, no GPU claim."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sp=importlib.util.spec_from_file_location('storage_extra_fixture_audit',ROOT/'research/healing-storage-extra-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
rows=[]
for name,b,x in d.fixtures():
    try:
        with d.v.s.v.context(name,x):
            c=d.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=d.v.s.v.v.a.evaluate(b)
        rows.append(dict(name=name,passed=True,total=cpu['total_damage'],effects=len(c['program']['effects'])))
    except Exception as e:rows.append(dict(name=name,passed=False,error=repr(e)))
    print(json.dumps(rows[-1],ensure_ascii=True),flush=True)
files=['research/audit-healing-storage-extra.py','research/healing-storage-extra-fixtures.py','scripts/verify-staged-healing-storage.py','research/probe-healing-storage-squads.py','research/staging/v40/app/healing_storage_compat.py','research/staging/v40/app/detail_gpu.py','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py']
r=dict(passed=all(x['passed'] for x in rows),cpu_model_extended=True,gpu_verified=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-healing-storage-extra-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
