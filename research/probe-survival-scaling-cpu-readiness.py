"""Discover CPU limitations before declaring a new GPU grammar accepted."""
import importlib.util,json,hashlib,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
staged='--staged' in sys.argv
if staged:
    loader_spec=importlib.util.spec_from_file_location('readiness_stage',ROOT/'scripts/staged-survival-scaling-runtime.py');loader=importlib.util.module_from_spec(loader_spec);loader_spec.loader.exec_module(loader);loader.install()
sp=importlib.util.spec_from_file_location('scaling_cpu_survival',ROOT/'scripts/verify-survival-detail.py');s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
rows=[]
for name in ('raw-목단-revival','raw-비스킷-revival','max-HP-scaled-revival'):
    if name.startswith('raw-'):
        character=name.split('-')[1];names=['라푼젤',s.N[0],s.N[1],character,s.N[3]];b=s.v.body(10,True,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[s.lethal('slot:4',2.8)];extra={}
    else:
        b=s.v.body(1);b['enemy']['patterns']=[s.lethal(at=.2)]
        extra={s.N[0]:[s.B('lost HP maximum','max_hp_only_pct',1.5,scaling='lost_hp_pct')],s.N[1]:[s.E('revive','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1)]}
    revived=[];original=s.CharState.on_revive
    def on_revive(self,t,bm):revived.append(dict(name=self.name,time=t));return original(self,t,bm)
    try:
        with s.v.context(name,extra),patch.object(s.CharState,'on_revive',on_revive):result=s.v.v.a.evaluate(b)
        r=dict(name=name,cpu_usable=True,total=result['total_damage'],revives=revived)
    except Exception as exc:r=dict(name=name,cpu_usable=False,error=repr(exc),revives=revived)
    rows.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
files=['research/probe-survival-scaling-cpu-readiness.py','app/survival_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
if staged:files+=['scripts/staged-survival-scaling-runtime.py','research/staging/v36/app/survival_scaling_compat.py']
destination='research/detail-survival-scaling-cpu-ready-staged.json' if staged else 'research/detail-survival-scaling-cpu-readiness.json'
(ROOT/destination).write_text(json.dumps(dict(objective_complete=False,gpu_verified=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if staged:assert all(r['cpu_usable'] and r['revives'] for r in rows)
