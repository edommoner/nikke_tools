"""Full actual A2 squads: mode drain/exit, healing, incoming and owned growth."""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_real_verifier',ROOT/'scripts/verify-hp-edge.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
g=v.g;s=v.s;N=v.N;B=v.B;E=v.E

def fixtures():
    for variant in ('dry-fixed','regular-heal','incoming','start-low','accumulate','mixed-growth','rapunzel-heal','rapunzel-revive'):
        names=[N[0],N[1],'A2',N[3],N[4]]
        if variant.startswith('rapunzel-'):names=['라푼젤',N[0],N[1],'A2',N[3]]
        b=s.v.body(60,True,names);b.update(burst_gauge_mode='fixed',_debug_hp_events=True)
        b['enemy']['patterns']=[s.lethal(at=100)];extra={n:[] for n in names}
        if variant=='regular-heal':extra[names[0]].append(E('periodic support','instant','heal_hp_pct',100,'all_allies',event='every:10s'))
        if variant=='incoming':
            b['enemy']['patterns']=[dict(id='damage',kind='attack',delay=2,until={'time':30},spec=dict(coeff=100,atk=500000,target='slot:3',hits=10,interval=2,pierce=True))]
            extra[names[0]].append(B('survival test support','undying',1,'all_allies'))
        if variant=='start-low':extra['A2'].append(E('test initial HP','instant','current_hp_reduce',75,event='battle_start'))
        if variant=='accumulate':b['burst_gauge_mode']='accumulate';b['seed']=7654321
        if variant=='mixed-growth':
            for i,n in enumerate(names):
                c=b['profile']['chars'][n];c.update(skill_levels={'1':3+i,'2':9-i,'3':10-i},affinity=1+6*i,core_enhancement=i,breakthrough=3)
                c['equip_skills']['atk_pct']=1+i
            b['stat_deltas']={'A2':{'atk':12000,'hp':100000,'def':250}}
        if variant=='rapunzel-revive':b['enemy']['patterns']=[s.lethal('slot:4',at=2.8)]
        yield 'raw-A2-'+variant,b,extra
    for character,variant in [('솔린 : 프로스트 티켓','counted-crossings'),('플로라','center'),('플로라','left'),('플로라','right')]:
        names=[N[0],N[1],character,N[3],N[4]]
        if variant=='left':names=[character,N[0],N[1],N[3],N[4]]
        if variant=='right':names=[N[0],N[1],N[3],N[4],character]
        b=s.v.body(30,True,names);b.update(burst_gauge_mode='fixed',_debug_hp_events=True);b['enemy']['patterns']=[s.lethal(at=100)]
        extra={n:[] for n in names}
        extra[names[0]]+=[E('controlled decrease','instant','current_hp_reduce',95 if variant=='counted-crossings' else 50,'all_allies',event='every:3s',max_trigger=3),E('controlled recovery','instant','heal_hp_pct',100,'all_allies',event='every:4s',max_trigger=3)]
        yield 'raw-'+character+'-'+variant,b,extra

def compare(device,name,b,extra,backend):
    events=[];removals=[];captured={};on_notify=v.BuffManager.notify;on_activate=v.BuffManager._activate;on_gpu=g.evaluate_full
    def notify(self,event,t,caster,**kwargs):
        if event in self._notify_index.get(caster,{}) and event.startswith(('hp_below:','event:ally_hp_below:','event:adjacent_hp_')):events.append(dict(event=event,time=t,caster=caster))
        return on_notify(self,event,t,caster,**kwargs)
    def activate(self,eff,caster,t,*args,**kwargs):
        if caster=='A2' and eff.get('stat')=='remove_named_buff':removals.append(dict(name=eff.get('name'),time=t))
        return on_activate(self,eff,caster,t,*args,**kwargs)
    def gpu(*args,**kwargs):
        result=on_gpu(*args,**kwargs);captured.update(result);return result
    with patch.object(v.BuffManager,'notify',notify),patch.object(v.BuffManager,'_activate',activate),patch.object(g,'evaluate_full',gpu):row=s.compare(device,name,b,extra,backend)
    row['checks']['hp_event_order']=s.v.close(captured.get('_hp_events'),events)
    if name in ('raw-A2-dry-fixed','raw-A2-incoming','raw-A2-start-low','raw-A2-accumulate','raw-A2-mixed-growth'):
        row['checks']['actual_HP_trigger_exercised']=bool(events) and bool(removals)
    if not name.startswith('raw-A2-'):row['checks']['actual_HP_trigger_exercised']=bool(events)
    row.update(cpu_hp_events=events,gpu_hp_events=captured.get('_hp_events'),cpu_A2_mode_removal_attempts=removals,passed=all(row['checks'].values()))
    print(json.dumps(dict(name=name,passed=row['passed'],failed=[k for k,value in row['checks'].items() if not value],cpu_hp_events=len(events),cpu_mode_removal_attempts=len(removals))),flush=True)
    return row

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],default='native');ap.add_argument('--output',default='research/detail-hp-edge-real-native.json');ap.add_argument('--fail-fast',action='store_true');args=ap.parse_args()
    files=['scripts/verify-hp-edge-real.py','scripts/verify-hp-edge.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/survival_compat.py','app/engine_compat.py','app/engine_worker.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']+['app/'+n for n in (('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json') if args.backend=='ptx' else ('detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'))]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};rows=[];planned=list(fixtures());device=s.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:row=compare(device,name,b,extra,args.backend)
            except Exception as exc:row=dict(name=name,passed=False,error=repr(exc));print(json.dumps(row),flush=True)
            rows.append(row)
            if args.fail_fast and not row['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(r['passed'] for r in rows),stage_only=False,objective_complete=False,abi=g.DETAIL_ABI,backend=args.backend,cases=rows,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
