"""Independent whole-squad CPU/GPU HP-transition acceptance for staged v35."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
import sys
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
s=load('hp_edge_survival_oracle','scripts/verify-survival-detail.py')
from calculator.buff_manager import BuffManager
N=s.N;B=s.B;E=s.E

def fixtures():
    for case in ('self-cross','already-below','rearm-after-heal','second-cross-counter','squad-observer-order','adjacent-observers','adjacent-max-transition','reentrant-heal'):
        b=s.v.body(1);b['_debug_hp_events']=True
        # A future attack creates frame witnesses without changing the battle.
        b['enemy']['patterns']=[s.lethal(at=100)]
        extra={n:[] for n in N};changed=N[1] if case.startswith('adjacent-') else N[0]
        extra[changed].append(E('reduce hp','instant','current_hp_reduce',50,'self',event='every:0.2s',max_trigger=2 if case in ('already-below','rearm-after-heal','second-cross-counter') else 1))
        if case in ('rearm-after-heal','second-cross-counter'):
            extra[changed].append(E('restore hp','instant','heal_hp_pct',100,'self',event='every:0.35s',max_trigger=1))
        timing='hp_below_count:60:2' if case=='second-cross-counter' else 'hp_below:60'
        extra[changed].append(B('self edge witness','atk_pct',17,event=timing,max_stack=100))
        if case=='squad-observer-order':
            for n in N:extra[n].append(B('squad edge witness','atk_pct',13,event='event:ally_hp_below:60'))
        if case in ('adjacent-observers','adjacent-max-transition','reentrant-heal'):
            for n in N:
                extra[n].append(B('adjacent low witness','atk_pct',11,event='event:adjacent_hp_below:60'))
                extra[n].append(B('adjacent max witness','atk_pct',7,event='event:adjacent_hp_max'))
        if case=='adjacent-max-transition':
            extra[changed].append(E('healing while full','instant','heal_hp_pct',100,'self',event='every:0.1s',max_trigger=1))
            extra[changed].append(E('recover maximum','instant','heal_hp_pct',100,'self',event='every:0.3s',max_trigger=1))
        if case=='reentrant-heal':extra[changed].append(E('heal inside edge','instant','heal_hp_pct',100,'self',event='hp_below:60'))
        yield case,b,extra
    for case in ('epsilon-cross','epsilon-no-cross','registration-high-first','registration-low-first','distinct-numeric-spellings','duplicate-key-descriptors','multiple-exact-counts','health-change-inside-edge','startup-max-hp-allies','max-hp-expiry','reduce-all-sequential','heal-all-sequential','lifesteal-to-max','incoming-crossings','received-heal-after-edge','revival-suppresses-edge'):
        b=s.v.body(2);b['_debug_hp_events']=True;b['enemy']['patterns']=[s.lethal(at=100)]
        extra={n:[] for n in N}
        def witness(n,timing,power=17):extra[n].append(B('edge witness '+str(len(extra[n])),'atk_pct',power,event=timing,max_stack=100))
        if case.startswith('epsilon-'):
            extra[N[0]].append(E('reduce hp','instant','current_hp_reduce',40,event='every:0.2s',max_trigger=1))
            witness(N[0],'hp_below:'+('59.9999995' if case=='epsilon-cross' else '59.999998'))
        elif case.startswith('registration-'):
            extra[N[0]].append(E('large decrease','instant','current_hp_reduce',80,event='every:0.2s',max_trigger=1))
            for threshold in ((80,40) if case.endswith('high-first') else (40,80)):witness(N[0],'hp_below:'+str(threshold),threshold)
        elif case in ('distinct-numeric-spellings','duplicate-key-descriptors','multiple-exact-counts'):
            extra[N[0]]+=[E('reduce hp','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=3),E('restore hp','instant','heal_hp_pct',100,event='every:0.15s',max_trigger=5)]
            if case=='distinct-numeric-spellings':
                for raw in ('60.0','60'):witness(N[0],'hp_below:'+raw)
            else:
                timings=['hp_below:60','hp_below_count:60:2'] if case=='duplicate-key-descriptors' else ['hp_below_count:60:2','hp_below_count:60:3']
                e=B('multiple timing witness','atk_pct',17,max_stack=100);e['trigger']['timing']=timings;extra[N[0]].append(e)
        elif case=='health-change-inside-edge':
            extra[N[0]]+=[E('reduce hp','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1),B('capacity inside edge','max_hp_only_pct',100,'all_allies',event='hp_below:60')]
            for n in N:witness(n,'hp_below:60');witness(n,'event:ally_hp_below:60')
        elif case in ('startup-max-hp-allies','max-hp-expiry'):
            extra[N[0]].append(B('capacity','max_hp_only_pct' if case.startswith('startup') else 'hp_only_caster_based_pct',100,'all_allies',**({} if case.startswith('startup') else dict(duration=.3))))
            for n in N:witness(n,'hp_below:80');witness(n,'event:adjacent_hp_max')
        elif case in ('reduce-all-sequential','heal-all-sequential'):
            extra[N[0]].append(E('decrease everyone','instant','current_hp_reduce',50,'all_allies',event='every:0.2s',max_trigger=1))
            if case=='heal-all-sequential':extra[N[0]].append(E('heal everyone','instant','heal_hp_pct',100,'all_allies',event='every:0.3s',max_trigger=1))
            for n in N:witness(n,'hp_below:60');witness(n,'event:ally_hp_below:60');witness(n,'event:adjacent_hp_below:60');witness(n,'event:adjacent_hp_max')
        elif case=='lifesteal-to-max':
            extra[N[0]]+=[E('reduce hp','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1),B('lifesteal','lifesteal_pct',100000)]
            for n in N:witness(n,'event:adjacent_hp_max')
        elif case in ('incoming-crossings','received-heal-after-edge'):
            b['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.2,until={'time':.8},spec=dict(coeff=100,atk=1000000 if case=='incoming-crossings' else 1,target='all',hits=3,interval=.2,pierce=True))]
            extra[N[0]].append(B('remain alive','undying',1,'all_allies'))
            if case=='received-heal-after-edge':extra[N[0]].append(E('decrease everyone','instant','current_hp_reduce',50,'all_allies',event='every:0.15s',max_trigger=1))
            for n in N:
                witness(n,'hp_below:90');witness(n,'event:ally_hp_below:90');witness(n,'event:adjacent_hp_max')
                if case=='received-heal-after-edge':extra[n].append(E('received heal','instant','heal_hp_pct',100,event='received_hit',max_trigger=1))
        else:
            b['enemy']['patterns']=[s.lethal(at=.2)]
            extra[N[1]].append(E('revive','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
            for n in N:witness(n,'hp_below:60');witness(n,'event:ally_hp_below:60');witness(n,'event:adjacent_hp_below:60');witness(n,'event:adjacent_hp_max')
        yield case,b,extra

def compare(device,name,body,extra,backend):
    events=[];activations=[];gpu_capture={};registered={n:set() for n in body['squad']}
    for n,effects in extra.items():
        for eff in effects:
            for timing in eff['trigger']['timing']:
                if timing.startswith('hp_below_count:'):timing='hp_below:'+timing.split(':')[1]
                registered[n].add(timing)
    original_notify=BuffManager.notify;original_activate=BuffManager._activate;original_gpu=g.evaluate_full
    def notified(self,event,t,caster,**kwargs):
        if event in registered.get(caster,set()) and event.startswith(('hp_below:','event:ally_hp_below:','event:adjacent_hp_')):
            events.append(dict(event=event,time=t,caster=caster))
        return original_notify(self,event,t,caster,**kwargs)
    def activated(self,eff,caster,t,*args,**kwargs):
        if 'witness' in eff.get('name',''):activations.append(dict(name=eff['name'],time=t,caster=caster))
        return original_activate(self,eff,caster,t,*args,**kwargs)
    def observed_gpu(*args,**kwargs):
        result=original_gpu(*args,**kwargs);gpu_capture.update(result);return result
    with patch.object(BuffManager,'notify',notified),patch.object(BuffManager,'_activate',activated),patch.object(g,'evaluate_full',observed_gpu):
        row=s.compare(device,name,body,extra,backend)
    basic=('self-cross','already-below','rearm-after-heal','second-cross-counter','squad-observer-order','adjacent-observers','adjacent-max-transition','reentrant-heal')
    if name in basic:
        self_events=[e for e in events if e['event']=='hp_below:60']
        expected=2 if name in ('rearm-after-heal','second-cross-counter') else 1
        row['checks']['cpu_crossing_positive_control']=len(self_events)==expected
        self_acts=[a for a in activations if a['name']=='self edge witness']
        row['checks']['cpu_activation_positive_control']=len(self_acts)==(1 if name=='second-cross-counter' else expected)
    else:
        row['checks']['cpu_crossing_positive_control']=bool(events)==(name not in ('epsilon-no-cross','revival-suppresses-edge'))
        if name not in ('epsilon-no-cross','revival-suppresses-edge'):row['checks']['cpu_activation_positive_control']=bool(activations)
    if '_hp_events' in gpu_capture:row['checks']['hp_event_order']=s.v.close(gpu_capture['_hp_events'],events)
    else:row['checks']['hp_event_order']=False
    row.update(cpu_hp_events=events,gpu_hp_events=gpu_capture.get('_hp_events'),cpu_witness_activations=activations)
    row['passed']=all(row['checks'].values())
    print(json.dumps(dict(name=name,passed=row['passed'],failed=[k for k,v in row['checks'].items() if not v]),ensure_ascii=True),flush=True)
    return row

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],default='native');ap.add_argument('--output',default='research/detail-hp-edge-native.json');ap.add_argument('--fail-fast',action='store_true');args=ap.parse_args()
    files=['scripts/verify-hp-edge.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/survival_compat.py','app/engine_compat.py','app/engine_worker.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']+['app/'+n for n in (('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json') if args.backend=='ptx' else ('detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'))]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};planned=list(fixtures());rows=[];device=s.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:row=compare(device,name,b,extra,args.backend)
            except Exception as exc:row=dict(name=name,passed=False,error=repr(exc));print(json.dumps(row),flush=True)
            rows.append(row)
            if args.fail_fast and not row['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files},'Sources changed while running.'
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(r['passed'] for r in rows),objective_complete=False,stage_only=False,abi=g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
