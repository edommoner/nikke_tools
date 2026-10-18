"""Mixed high-ID masks and an empty program in actual concurrent native batches."""
import hashlib,importlib.util,json,math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('named_mask_batch',ROOT/'scripts/verify-named-capacity-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
if __name__=='__main__':
    files=['scripts/verify-named-capacity-batch.py','scripts/verify-named-capacity-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
    def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    hashes={p:sha(p) for p in files}
    items=list(v.primitives());script=items[0][2]
    empty=v.v.oracle.program(v.v.oracle.characters(v.v.NAMES),[])
    items.insert(3,('empty-between-dense-programs',empty,script,[0,0,0]))
    stats={n:{'atk':100000,'def':20000,'hp':1000000} for n in v.v.NAMES};rows=[];launches=0
    device=v.Cuda()
    try:
        for start in range(0,len(items),8):
            batch=items[start:start+8];assert all(s==script for _,p,s,_ in batch)
            gpu=v.g.run(device,[p for _,p,_,_ in batch],script,[[31784,0] for _ in batch],[stats for _ in batch],module_backend='native');launches+=1
            for index,(name,p,commands,expected) in enumerate(batch):
                cpu,totals=v.v.oracle.oracle(p,commands,[31784,0],stats)
                errors=[[i,k,x[k],y[k]] for i,(x,y) in enumerate(zip(cpu,gpu['queries'][index])) for k in list(range(32))+[36,37] if not math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8)]
                checks=dict(queries=not errors,totals=totals==gpu['totals'][index],expected_atk=[x[0] for x in cpu]==[x[0] for x in gpu['queries'][index]]==expected)
                row=dict(name=name,batch_size=len(batch),backend=gpu['module_backend'],effects=len(p['effects']),passed=all(checks.values()),checks=checks,errors=errors[:16])
                rows.append(row);print(json.dumps(row),flush=True)
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==33 and all(r['passed'] for r in rows),cases=rows,launches=launches,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,scope='Native concurrent batches of distinct state-ID/sign masks, including empty and full-capacity programs. PTX semantic parity is checked separately.')
    (ROOT/'research/detail-named-capacity-batch-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
