"""CPU and compiler preflight, with no GPU execution or parity claim."""
import hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sp=importlib.util.spec_from_file_location('outgoing_fixtures',ROOT/'scripts/verify-staged-outgoing-healing.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
rows=[];original=m.BuffManager.heal_received_mult
for name,b,extra in list(m.fixtures())+list(m.real_fixtures(include_unsupported=True)):
    calls=[]
    def observe(self,who,t,**kwargs):
        r=original(self,who,t,**kwargs);calls.append(dict(recipient=who,source=kwargs.get('heal_source'),time=t,multiplier=r));return r
    try:
        with m.v.s.v.context(name,extra),patch.object(m.BuffManager,'heal_received_mult',observe):
            c=m.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=m.v.s.v.v.a.evaluate(b)
        expected={'source-only':1.5,'recipient-is-not-source':1,'separate-layers':1.875,'additive-sources':1.75,'negative-source':0,'negative-recipient':0,'stacked-source':2.5,'periodic':1.5,'caster-max':1.5,'duplicates':1.5,'expired':1,'lazy-target':1.5,'conditional':1.5,'lifesteal':1.5,'lifesteal-negative':0,'registered-timer-source-down':1}
        case=name.removeprefix('outgoing-');checks={}
        if case in expected:
            checks['hand_derived_multiplier']=bool(calls) and all(q['multiplier']==expected[case] for q in calls)
            checks['original_healer_source']=all(q['source']==m.N[1] for q in calls)
        elif name.endswith('-unaffected'):checks['repair_does_not_query_body_multiplier']=not calls
        elif name.startswith('raw-'):
            checks['actual_raw_healing_exercised']=bool(calls)
            checks['actual_outgoing_bonus_exercised']=any(q['multiplier']>1 for q in calls)
            if name.endswith('owned-healing-cube'):
                checks['actual_cube_carrier_in_gpu_program']=any(q[1]==0 and q[2]==73 and q[6]==12.12 for q in c['program']['effects'])
        rows.append(dict(name=name,passed=all(checks.values()),checks=checks,total=cpu['total_damage'],effect_rows=len(c['program']['effects']),queries=calls))
    except m.g.UnsupportedDetail as e:
        expected='heal_overcharge_store' if '-소라-' in name else 'shield_dmg_pct' if '-미사토-' in name else None
        rows.append(dict(name=name,passed=bool(expected and expected in str(e)),expected_rejection=expected,error=repr(e)))
    except Exception as e:rows.append(dict(name=name,passed=False,error=repr(e)))
    print(json.dumps({k:v for k,v in rows[-1].items() if k!='queries'},ensure_ascii=True),flush=True)
files=['research/audit-outgoing-healing-fixtures.py','scripts/verify-staged-outgoing-healing.py','scripts/staged-outgoing-healing-runtime.py','research/staging/v39/app/detail_gpu.py','research/staging/v39/app/outgoing_healing_compat.py','research/staging/v39/app/detail_effects.cu','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
r=dict(passed=all(x['passed'] for x in rows),gpu_verified=False,objective_complete=False,cpu_model_extended=True,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-outgoing-healing-fixture-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
