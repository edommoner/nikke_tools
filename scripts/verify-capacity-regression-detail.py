"""Share one CUDA context across catalog, owned-data and long v29 regressions."""
import argparse,hashlib,importlib.util,json,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
catalog=load('capacity_catalog','scripts/verify-catalog-batch-detail.py')
owned=load('capacity_owned','scripts/verify-owned-detail.py')
capacity=load('capacity_long','scripts/verify-capacity-detail.py')
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def save(path,report,hashes):
    assert all(sha(p)==h for p,h in hashes.items()),'Sources changed during verification'
    report['source_sha256']={**report.get('source_sha256',{}),**hashes}
    (ROOT/path).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert report['passed'],path
if __name__=='__main__':
    files=['scripts/verify-capacity-regression-detail.py','scripts/verify-capacity-detail.py','scripts/verify-owned-detail.py','scripts/verify-catalog-batch-detail.py','scripts/verify-full-detail.py','scripts/detail_coverage.py','research/detail-charge-immunity-api-fixture.json','research/detail-team-hits-api-fixture.json','research/ports/v28/research/detail-capacity-cpu-audit.json','app/detail_gpu.py','app/detail_world.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py']
    hashes={p:sha(p) for p in files}
    previous=ROOT/'research/detail-owned-acceptance.json';archive=ROOT/'research/ports/v28/research/detail-owned-acceptance.json'
    if previous.exists() and not archive.exists():archive.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(previous,archive)
    device=catalog.Cuda();close=device.close;device.close=lambda:None
    try:
        # Dependency injection only shares the device; battle inputs and independent
        # CPU comparison logic remain in the original verifiers.
        catalog.Cuda=lambda:device
        args=argparse.Namespace(backend='both',batch_size=8,duration=30,seed=12345,mode='fixed',shooting_policy='auto',character=None,limit=None)
        save('research/detail-catalog-capacity-verification.json',catalog.main(args),hashes)
        cases=[r for backend in ('native','ptx') for r in owned.verify(device,backend)]
        controls=owned.positive_controls(cases)
        save('research/detail-owned-acceptance.json',dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(cases) and all(r['passed'] for r in cases) and all(all(c.values()) for c in controls.values()),cases=cases,positive_controls=controls,cpu_trace_used_as_gpu_input=False,scope='Fictional owned profiles, growth/stat deltas, position order, automatic/cycle burst and charge operation; 18 settings per backend.'),hashes)
        cases=capacity.verify_battles(device,'native',long=True)
        save('research/detail-capacity-long-verification.json',dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in cases),cases=cases,duration=180,backend='native',cpu_trace_used_as_gpu_input=False),hashes)
    finally:close()
