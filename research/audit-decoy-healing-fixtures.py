"""Compile and CPU preflight; not GPU acceptance."""
import hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('decoy_preflight',ROOT/'scripts/verify-staged-decoy-healing.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
rows=[]
for name,b,extra in list(v.fixtures())+list(v.real_fixtures()):
    heals=[];original=v.BuffManager.heal_decoy
    def heal(self,who,amount,t):
        out=original(self,who,amount,t);heals.append(dict(time=t,recipient=who,amount=amount,actual=out));return out
    try:
        with v.v.s.v.context(name,extra),patch.object(v.BuffManager,'heal_decoy',heal):
            compiled=v.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=v.v.s.v.v.a.evaluate(b)
        row=dict(name=name,compiled=True,cpu_usable=True,total=cpu['total_damage'],heals=len(heals),positive_heals=sum(h['actual']>0 for h in heals))
    except Exception as exc:row=dict(name=name,compiled=False,cpu_usable=False,error=repr(exc))
    rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
files=['research/audit-decoy-healing-fixtures.py','scripts/verify-staged-decoy-healing.py','scripts/staged-decoy-healing-runtime.py','research/staging/v38/app/detail_gpu.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
r=dict(passed=all(x['compiled'] and x['cpu_usable'] for x in rows),gpu_verified=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-decoy-healing-fixture-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
