"""Nested cleanse during creation/refresh, without changing real source skills."""
import hashlib,importlib.util,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('nested_cleanse',ROOT/'scripts/verify-cleanse-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import evaluate_full
E=v.v.E;NAMES=v.v.NAMES
def scenarios():
 owner=NAMES[0]
 for label,target,timing in [('shield-stack-partial','self','stack_reach:nested harm:1'),('shield-event-complete','all_allies','event:nested harm')]:
  yield label,{owner:[E('shield gate','buff','atk_pct',100,'all_allies',event='passive',condition=['during_shield']),E('nested harm','buff','shield_from_max_hp_pct',50,'all_allies',polarity='harmful'),E('nested cleanse','instant','debuff_cleanse',1,target,event=timing)]}
 effects={n:[E('named recipient probe','buff','atk_pct',7,event='event:stacking harm',max_stack=100)] for n in NAMES}
 effects[owner]+=[E('stacking harm','buff','atk_pct',-10,'all_allies',polarity='harmful',event='every:1s',max_stack=3,event_scope='recipients'),E('nested cleanse','instant','debuff_cleanse',1,'self',event='stack_reach:stacking harm:2')]
 yield 'refresh-updates-named-recipient-audience',effects
 yield 'max-hp-creation-partial',{owner:[E('hp harm','buff','max_hp_only_pct',100,'all_allies',polarity='harmful'),E('nested cleanse','instant','debuff_cleanse',1,'self',event='stack_reach:hp harm:1'),E('below hp probe','buff','atk_pct',50,'all_allies',event='passive',condition=['self_hp_below:80'])]}

def verify(device,backend):
 rows=[]
 for name,effects in scenarios():
  for mode in ('fixed','accumulate'):
   body=v.v.c.body_for(NAMES,8,True);body['burst_gauge_mode']=mode
   with v.v.c.p.custom_effects(effects):
    compiled=v.v.c.a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend)
    with v.v.c.observe() as (_,manager,_),v.v.observe() as cleanups:cpu=v.v.c.a.evaluate(body)
   checks={k:cpu[k]==gpu[k] for k in ('total_damage','members','base_stats','burst_timeline','burst_gauge_mode')};checks['cleanse_exercised']=bool(cleanups)
   bm=manager['bm'];health={n:{'hp':bm.state['hp'][n],'hp_pct':bm.state['hp_pct'][n],'max_hp':bm.effective_max_hp(n)} for n in NAMES}
   checks['final_health']=all(math.isclose(health[n][key],gpu['compute']['final_hp'][n][key],rel_tol=1e-12,abs_tol=1e-6) for n in NAMES for key in health[n])
   row=dict(name=name+'-'+mode,backend=backend,passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],cpu_health=health,gpu_health=gpu['compute']['final_hp']);rows.append(row);print(json.dumps(row),flush=True)
 return rows
if __name__=='__main__':
 native_only='--native-only' in sys.argv;d=v.v.c.Cuda()
 try:rows=verify(d,'native')+([] if native_only else verify(d,'ptx'))
 finally:d.close()
 files=['scripts/verify-cleanse-nested.py','scripts/verify-cleanse-detail.py','scripts/audit-debuff-cleanse.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-build.json','app/detail_effects-sm86.json']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),cpu_trace_used_as_gpu_input=False,native_only=native_only,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 suffix='native' if native_only else 'verification'
 (ROOT/f'research/detail-cleanse-nested-{suffix}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
