"""v30 regressions grouped by backend to avoid repeated PTX recompilation."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
named=load('named_capacity_combined','scripts/verify-named-capacity-detail.py')
cap=load('capacity_combined','scripts/verify-capacity-detail.py')
catalog=load('named_catalog_combined','scripts/verify-catalog-batch-detail.py')
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def report(rows,hashes,**kw):return dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(rows) and all(r['passed'] for r in rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,objective_complete=False,**kw)
def save(path,r,hashes):
    assert all(sha(p)==h for p,h in hashes.items()),'Sources changed during verification'
    r['source_sha256']={**r.get('source_sha256',{}),**hashes}
    (ROOT/path).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert r['passed'],path
if __name__=='__main__':
    initial='research/detail-named-capacity-native.json';native=json.loads((ROOT/initial).read_text(encoding='utf-8'))
    assert native['passed'] and len(native['cases'])==38 and all(sha(p)==h for p,h in native['source_sha256'].items())
    files=list(native['source_sha256'])+['scripts/verify-named-capacity-regression.py','scripts/verify-capacity-detail.py','scripts/verify-catalog-batch-detail.py','scripts/detail_coverage.py',initial,'research/detail-team-hits-api-fixture.json','research/ports/v28/research/detail-capacity-cpu-audit.json','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
    hashes={f:sha(f) for f in files};device=named.Cuda();close=device.close;device.close=lambda:None
    catalogs=[];capacity=[]
    try:
        capacity.extend(cap.verify_primitives(device,'native')+cap.verify_battles(device,'native'))
        catalog.Cuda=lambda:device
        args=argparse.Namespace(backend='native',batch_size=8,duration=30,seed=12345,mode='fixed',shooting_policy='auto',character=None,limit=None)
        catalogs.append(catalog.main(args));assert catalogs[-1]['passed']
        rows=native['cases']+named.verify_primitives(device,'ptx')+named.verify_battles(device,'ptx')
        save('research/detail-named-capacity-verification.json',report(rows,hashes),hashes)
        capacity.extend(cap.verify_primitives(device,'ptx')+cap.verify_battles(device,'ptx'))
        save('research/detail-capacity-named-mask-verification.json',report(capacity,hashes),hashes)
        args.backend='ptx';catalogs.append(catalog.main(args));assert catalogs[-1]['passed']
        combined={**catalogs[0],'cases':[r for c in catalogs for r in c['cases']],'not_executed':[r for c in catalogs for r in c['not_executed']]}
        save('research/detail-catalog-named-capacity-verification.json',combined,hashes)
        low=named.v.verify(device,'ptx')
        save('research/detail-named-low-ptx-verification.json',report(low,hashes),hashes)
        long=named.verify_battles(device,'native',long=True)
        save('research/detail-named-capacity-long-verification.json',report(long,hashes,duration=180),hashes)
    finally:close()
