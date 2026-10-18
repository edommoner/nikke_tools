"""Native 180-second raw D/Rumani regression across repeated burst/expiry cycles."""
import copy,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('team_long',ROOT/'scripts/verify-team-hits-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

if __name__=='__main__':
    files=['scripts/verify-team-hits-long-detail.py','scripts/verify-team-hits-detail.py','app/detail_gpu.py','app/detail_world.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    templates=[copy.deepcopy(case) for case in v.bodies() if case[2]=='live' and case[1]['shooting_policy']=='character' and case[1]['burst_gauge_mode']=='accumulate']
    assert len(templates)==2
    combined=copy.deepcopy(templates[0][1])
    combined['squad'][1]='루마니'
    combined['profile']['chars']['루마니']=combined['profile']['chars'].pop('리타')
    templates.append(('combined-D-Rumani-live',combined,'live',{}))
    for _,body,_,_ in templates:body['duration']=180
    v.bodies=lambda quick=False:iter(templates)
    device=v.Cuda()
    try:rows=v.verify_battles(device,'native')
    finally:device.close()
    for row in rows:
        row['checks']['multiple_b3_bonus_cycles']=len(row['b3_bonus_dispatches'])>=2
        row['passed']=all(row['checks'].values())
    assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'Sources changed during verification'
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),backend='native',duration=180,cases=rows,cpu_trace_used_as_gpu_input=False,source_sha256=hashes)
    (ROOT/'research/detail-team-hits-long-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
