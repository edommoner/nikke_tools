"""Pure CPU witnesses for the next HP-edge event port; no GPU claim."""
import hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_edge_reference',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
from calculator.buff_manager import BuffManager
N=v.NAMES;rows=[]
for case in ('self-cross','already-below','rearm-after-heal','second-cross-counter','squad-observer-order','adjacent-observers','adjacent-max-transition','reentrant-heal'):
    b=v.body(1);b['enemy']['patterns']=[];extra={n:[] for n in N};changed=N[1] if case.startswith('adjacent-') else N[0]
    extra[changed].append(v.E('reduce hp','instant','current_hp_reduce',50,'self',event='every:0.2s',max_trigger=2 if case in ('already-below','rearm-after-heal','second-cross-counter') else 1))
    if case in ('rearm-after-heal','second-cross-counter'):
        extra[changed].append(v.E('restore hp','instant','heal_hp_pct',100,'self',event='every:0.35s',max_trigger=1))
    timing='hp_below_count:60:2' if case=='second-cross-counter' else 'hp_below:60'
    extra[changed].append(v.B('self edge witness','atk_pct',1,event=timing,max_stack=100))
    if case=='squad-observer-order':
        for n in N:extra[n].append(v.B('squad edge witness','atk_pct',1,event='event:ally_hp_below:60'))
    if case in ('adjacent-observers','adjacent-max-transition','reentrant-heal'):
        for n in N:
            extra[n].append(v.B('adjacent low witness','atk_pct',1,event='event:adjacent_hp_below:60'))
            extra[n].append(v.B('adjacent max witness','atk_pct',1,event='event:adjacent_hp_max'))
    if case=='adjacent-max-transition':
        extra[changed].append(v.E('healing while full','instant','heal_hp_pct',100,'self',event='every:0.1s',max_trigger=1))
        extra[changed].append(v.E('recover maximum','instant','heal_hp_pct',100,'self',event='every:0.3s',max_trigger=1))
    if case=='reentrant-heal':extra[changed].append(v.E('heal inside edge','instant','heal_hp_pct',100,'self',event='hp_below:60'))
    events=[];activations=[];original_notify=BuffManager.notify;original_activate=BuffManager._activate
    def notified(self,event,t,caster,**kwargs):
        if event.startswith(('hp_below:','event:ally_hp_below:','event:adjacent_hp_')):events.append(dict(event=event,time=t,caster=caster))
        return original_notify(self,event,t,caster,**kwargs)
    def activated(self,eff,caster,t,*args,**kwargs):
        if 'witness' in eff.get('name',''):activations.append(dict(name=eff['name'],time=t,caster=caster))
        return original_activate(self,eff,caster,t,*args,**kwargs)
    with v.context('controlled',extra),patch.object(BuffManager,'notify',notified),patch.object(BuffManager,'_activate',activated):cpu=v.v.a.evaluate(b)
    self_events=[e for e in events if e['event']=='hp_below:60']
    assert len(self_events)==(2 if case in ('rearm-after-heal','second-cross-counter') else 1),(case,events)
    self_activations=[e for e in activations if e['name']=='self edge witness']
    assert len(self_activations)==(1 if case=='second-cross-counter' else len(self_events)),(case,activations)
    if case=='squad-observer-order':assert [e['caster'] for e in events if e['event']=='event:ally_hp_below:60']==N
    if case.startswith('adjacent-'):
        assert [e['caster'] for e in events if e['event']=='event:adjacent_hp_below:60']==[N[0],N[2]],events
    if case=='adjacent-max-transition':assert [e['caster'] for e in events if e['event']=='event:adjacent_hp_max']==[N[0],N[2]],events
    if case=='reentrant-heal':assert not any(e['event']=='event:adjacent_hp_max' for e in events),events
    row=dict(name=case,cpu_reference_verified=True,gpu_implemented=False,events=events,activation_attempts=activations,total=cpu['total_damage']);rows.append(row)
    print(json.dumps(dict(name=case,passed=True,gpu_implemented=False)),flush=True)
files=['scripts/audit-hp-edge-events.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-hp-edge-cpu-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
