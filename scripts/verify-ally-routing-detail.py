"""Additional recipient routes: special ATK, grouped charge and enemy stats."""
import hashlib, importlib.util, json, math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ally_routing',ROOT/'scripts/verify-ally-conditions-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def cases():
    for stat,target in [('atk_caster_based_pct','all_allies'),('charge_speed_pct','all_allies'),('crit_rate','all_allies'),('received_dmg_pct','boss'),('def_pct','boss'),('charge_speed_caster_based_pct','all_allies')]:
        owner=v.NAMES[4] if stat=='charge_speed_caster_based_pct' else v.NAMES[0]
        effects=[(v.E('routing gate','buff',stat,23,target,event='passive',condition=['ally_hp_below:50']),owner),
                 (v.E('routing drain','instant','current_hp_reduce',50,v.NAMES[2],event='burst_cast'),v.NAMES[1])]
        commands=[(0,0,i) for i in range(5)]+[(.1,3,1)]+[(.2,'query',i) for i in [4,2,0,3,1]]
        yield stat+'-'+target,v.NAMES,effects,commands,None

if __name__=='__main__':
    rows=[]
    device=v.Cuda()
    try:
        for name,names,effects,commands,_ in cases():
            program=v.oracle.program(v.oracle.characters(names),effects)
            stats={n:{'atk':100000+i*1234,'hp':1000000,'def':1000} for i,n in enumerate(names)}
            script=[];index=0
            for t,event,who in commands:
                script.append([t,2 if event=='query' else 0,0 if event=='query' else event,who,-1,index if event=='query' else -1,0,0])
                if event=='query':index+=1
            cpu,_=v.cpu_oracle(program,script,[31784,50],stats)
            gpu=v.run(device,[program],script,[[31784,50]],[stats],module_backend='native')['queries'][0]
            # The legacy CPU oracle deliberately zeros diagnostic column 26:
            # caster-based ATK is converted into canonical flat ATK (column 1).
            # Check that actual flat ATK and independently calculated damage.
            columns=[k for k in range(32) if k!=26]+[36]
            errors=[[i,k,x[k],y[k]] for i,(x,y) in enumerate(zip(cpu,gpu)) for k in columns if not math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-9)]
            assert len(cpu)==len(gpu)==5
            stat=effects[0][0]['stat']
            if stat=='atk_caster_based_pct':assert cpu[1][1]>0 and all(q[1]==0 for i,q in enumerate(cpu) if i!=1)
            if stat in ('charge_speed_pct','charge_speed_caster_based_pct'):assert cpu[1][20]>0 and all(q[20]==0 for i,q in enumerate(cpu) if i!=1)
            if stat=='crit_rate':assert cpu[1][5]>.15 and all(q[5]==.15 for i,q in enumerate(cpu) if i!=1)
            row=dict(name=name,backend='native',passed=not errors,errors=errors,
                     cpu_flat_atk=[q[1] for q in cpu],gpu_flat_atk=[q[1] for q in gpu],
                     cpu_charge=[q[20] for q in cpu],gpu_charge=[q[20] for q in gpu],
                     cpu_damage=[q[36] for q in cpu],gpu_damage=[q[36] for q in gpu])
            rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    finally:device.close()
    files=['scripts/verify-ally-routing-detail.py','scripts/verify-ally-conditions-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json']
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==6 and all(r['passed'] for r in rows),cases=rows,excluded_diagnostic_column=26,canonical_flat_atk_and_damage_checked=True,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},cpu_trace_used_as_gpu_input=False)
    (ROOT/'research/detail-ally-routing-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
