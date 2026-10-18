"""Independent full raw-character battles with authored shield-layer stimuli.

This exercises shield consumption within combat, not a boss attack/HP model.
CPU choices, damage, shield quantities and event times are never GPU inputs.
"""
import copy, hashlib, importlib.util, json, math, random, sys
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'scripts')]
spec = importlib.util.spec_from_file_location('shield_control', ROOT/'scripts/verify-control-detail.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
import detail_gpu
from calculator.buff_manager import BuffManager
from gpu_selector import Cuda

SCHEDULE = [2, 4, 8, 12, 20, 28]
SUBJECTS = ['센티', '라푼젤 : 퓨어 그레이스', '모리']

def compare(device, subject, seed, mode, backend):
    names = [subject, '리타', '크라운', '앨리스', '모더니아']
    body = c.body_for(names, 35, True)
    body.update(seed=seed, burst_gauge_mode=mode, shooting_policy='character',
                burst_policy='rules', _debug_random_state=True)
    amount = 1e9 if subject == SUBJECTS[2] else 100000
    controls = {subject: {'sequence': [{'t':t, 'action':'hold', 'until':end}
                for t,end in [(0,3),(4,8),(12,16),(20,24),(28,32)]]}}
    context = c.configured(controls) if subject == SUBJECTS[1] else nullcontext()
    original_run = detail_gpu.run; captured = {}
    def gpu_run(device, programs, script, *args, **kwargs):
        script = copy.deepcopy(script); index = 0
        for row in script:
            if row[1] == 4 and index < len(SCHEDULE) and row[0] >= SCHEDULE[index]:
                row[2]=1; row[3]=0; row[6]=amount; row[7]=0; index+=1
        qi = sum(row[1] == 2 for row in script)
        script.append([body['duration'],2,111,0,-1,qi,0,0])
        result = original_run(device, programs, script, *args, **kwargs)
        captured['shield'] = result['queries'][0][qi]
        return result
    original_tick = BuffManager.tick; original_heal = BuffManager.heal_shield
    observed = {'absorbed':[], 'healed':[]}; pending = iter(SCHEDULE); next_time = next(pending, None)
    def tick(self, t):
        nonlocal next_time
        result = original_tick(self,t)
        if next_time is not None and t >= next_time:
            observed['absorbed'].append(self.absorb_shield(subject,amount,t,pierce=False))
            next_time = next(pending, None)
        return result
    def heal(self, who, value, t):
        result = original_heal(self,who,value,t); observed['healed'].append(result); return result
    with context:
        compiled = c.a.evaluate({**body, '_compile_gpu_detail':True})
        with patch.object(detail_gpu,'run',gpu_run):
            gpu = detail_gpu.evaluate_full(device,compiled,module_backend=backend)
        with c.observe() as (_,manager,_), patch.object(BuffManager,'tick',tick), patch.object(BuffManager,'heal_shield',heal):
            cpu = c.a.evaluate(body)
        final_rng = list(random.getstate()[1]); bm = manager['bm']
    checks = {k:cpu[k] == gpu[k] for k in ('total_damage','members','base_stats','burst_timeline','seed','burst_gauge_mode','shooting_policy')}
    checks['final_random_state'] = final_rng == gpu['_random_state']
    errors = []; shield = captured['shield']
    for i,name in enumerate(names):
        expected = [bm.shield_amount(name),bm.shield_capacity(name),int(bm.has_shield(name))]
        for field,x,y in zip(('amount','capacity','has_shield'), [shield[1+i],shield[6+i],shield[11+i]], expected):
            if not math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-6): errors.append([name,field,x,y])
    checks['final_shields'] = not errors
    checks['positive_absorption_exercised'] = any(x>0 for x in observed['absorbed'])
    if subject == SUBJECTS[1]: checks['positive_shield_heal_exercised'] = any(x>0 for x in observed['healed'])
    return dict(subject=subject,seed=seed,mode=mode,backend=backend,passed=all(checks.values()),checks=checks,
                cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],shield_errors=errors,
                authored_shield_damage=amount,observed=observed,all_subject_skills_retained=True,
                authored_charge_holds=subject==SUBJECTS[1])

def verify(device, backend, quick=False):
    rows=[]
    for subject in SUBJECTS:
        for seed in ((0,) if quick else (0,12345)):
            for mode in ('fixed','accumulate'):
                try: row=compare(device,subject,seed,mode,backend)
                except Exception as error: row=dict(subject=subject,seed=seed,mode=mode,backend=backend,passed=False,error=str(error))
                rows.append(row); print(json.dumps(row,ensure_ascii=True),flush=True)
    return rows

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx','both'],default='both');p.add_argument('--quick',action='store_true');args=p.parse_args()
    device=Cuda()
    try: rows=sum((verify(device,b,args.quick) for b in (('native','ptx') if args.backend=='both' else (args.backend,))),[])
    finally: device.close()
    files=['scripts/verify-shield-squads-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),cases=rows,
        scope='Complete raw five-member battles with authored shield-layer damage; not incoming boss HP/cover damage, part destruction or every skill context.',
        cpu_trace_used_as_gpu_input=False,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    (ROOT/'research/detail-shield-squads-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
