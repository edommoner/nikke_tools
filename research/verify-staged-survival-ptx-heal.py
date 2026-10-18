"""PTX-only healing check, safe alongside the independent native build."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('heal_query_check',ROOT/'scripts/verify-staged-heal-query.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
files=list(json.loads((ROOT/'research/detail-staged-survival-initial-quick.json').read_text(encoding='utf-8'))['source_sha256'])+['scripts/verify-staged-heal-query.py','research/verify-staged-survival-ptx-heal.py']
files=[p for p in files if 'detail_effects-sm86.' not in p]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files}
rows=[];d=m.m.v.v.v.Cuda()
try:
    for name,b,extra in m.fixtures():
        try:row=m.m.compare(d,name,b,extra,'ptx')
        except Exception as error:row=dict(name=name,passed=False,error=repr(error));print(json.dumps(row),flush=True)
        rows.append(row)
finally:d.close()
assert hashes=={p:sha(p) for p in files}
r=dict(passed=all(x['passed'] for x in rows),objective_complete=False,stage_only=True,cases=rows,source_sha256=hashes)
(ROOT/'research/detail-staged-survival-ptx-heal-early.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if r['passed'] else 1)
