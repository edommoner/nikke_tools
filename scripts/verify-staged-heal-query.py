"""Positive controls for lazy healing recipients, with actual GPU/CPU parity."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('heal_survival_oracle',ROOT/'scripts/verify-staged-survival.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixtures():
    for target in ('allies_lowest_hp:1','allies_top_atk:2','allies_lowest_hp_excl:2'):
        b=m.v.body(1)
        b['enemy']['patterns']=[m.lethal(at=100)]
        extra={m.N[0]:[
            m.B('lazy received healing','heal_received_pct',80,target,event='every:0.2s',duration=1),
            m.E('make room','instant','current_hp_reduce',50,'all_allies',event='every:0.3s',max_trigger=1),
            m.E('delayed heal','instant','heal_hp_pct',10,'all_allies',event='every:0.4s',max_trigger=1)
        ]}
        yield 'healing-query-'+target,b,extra

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],default='native');ap.add_argument('--output',required=True);args=ap.parse_args()
    files=list(json.loads((ROOT/'research/detail-staged-survival-initial-quick.json').read_text(encoding='utf-8'))['source_sha256'])+['scripts/verify-staged-heal-query.py']
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    hashes={p:sha(p) for p in files};planned=list(fixtures());rows=[];device=m.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:row=m.compare(device,name,b,extra,args.backend)
            except Exception as error:row=dict(name=name,passed=False,error=repr(error));print(json.dumps(row),flush=True)
            rows.append(row)
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),objective_complete=False,stage_only=True,abi=m.g.DETAIL_ABI,cases=rows,planned_cases=len(planned),not_run_cases=0,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
