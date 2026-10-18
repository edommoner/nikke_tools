"""Validate authored HP-edge fixtures independently before the GPU run."""
import hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hp_fixtures',ROOT/'scripts/verify-staged-hp-edge.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
rows=[]
for name,b,extra in v.fixtures():
    events=[];acts=[];on_notify=v.BuffManager.notify;on_activate=v.BuffManager._activate
    def notify(self,event,t,caster,**kwargs):
        if event.startswith(('hp_below:','event:ally_hp_below:','event:adjacent_hp_')):events.append(dict(event=event,time=t,caster=caster))
        return on_notify(self,event,t,caster,**kwargs)
    def activate(self,eff,caster,t,*args,**kwargs):
        if 'witness' in eff.get('name',''):acts.append(dict(name=eff['name'],time=t,caster=caster))
        return on_activate(self,eff,caster,t,*args,**kwargs)
    try:
        with v.s.v.context(name,extra),patch.object(v.BuffManager,'notify',notify),patch.object(v.BuffManager,'_activate',activate):
            compiled=v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=v.s.v.v.a.evaluate(b)
        row=dict(name=name,compiled=True,cpu_verified=True,gpu_verified=False,events=events,activation_attempts=acts,total=cpu['total_damage'])
    except Exception as exc:row=dict(name=name,compiled=False,cpu_verified=False,gpu_verified=False,error=repr(exc))
    rows.append(row);print(json.dumps(dict(name=name,compiled=row['compiled'],cpu_verified=row['cpu_verified'],events=len(events),witness_activations=len(acts),**({'error':row['error']} if 'error' in row else {}))),flush=True)
files=['scripts/verify-staged-hp-edge.py','research/probe-hp-edge-cpu-fixtures.py','research/staging/v35/app/detail_gpu.py','app/engine_compat.py','app/survival_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
r=dict(cpu_verified=all(x['cpu_verified'] for x in rows),gpu_verified=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-hp-edge-expanded-cpu-fixtures.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if r['cpu_verified'] else 1)
