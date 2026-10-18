"""Compile/CPU preflight for v37; no GPU acceptance claim."""
import hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('capacity_preflight',ROOT/'scripts/verify-staged-cover-capacity.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
rows=[]
for name,b,extra in list(v.fixtures())+list(v.real_fixtures()):
    changes=[];original=v.BuffManager.sync_cover_hp
    def sync(self,who,t):
        before=self.state['cover_max_hp'][who];result=original(self,who,t);after=self.state['cover_max_hp'][who]
        if before!=after:changes.append(dict(time=t,character=who,before=before,after=after,base=self.state['cover_base_hp'][who]))
        return result
    try:
        with v.v.s.v.context(name,extra),patch.object(v.BuffManager,'sync_cover_hp',sync):
            compiled=v.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=v.v.s.v.v.a.evaluate(b)
        row=dict(name=name,compiled=True,cpu_usable=True,total=cpu['total_damage'],capacity_changes=len(changes),capacity_exercised=any(c['after']!=c['base'] for c in changes))
    except Exception as exc:row=dict(name=name,compiled=False,cpu_usable=False,error=repr(exc))
    rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
files=['research/audit-cover-capacity-fixtures.py','scripts/verify-staged-cover-capacity.py','scripts/staged-cover-capacity-runtime.py','research/staging/v37/app/detail_gpu.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
r=dict(passed=all(x.get('compiled') and x.get('cpu_usable') and x.get('capacity_exercised') for x in rows),gpu_verified=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-cover-capacity-fixture-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
