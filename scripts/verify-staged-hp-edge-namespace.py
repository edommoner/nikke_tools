"""Keep real HP crossings distinct from similarly named explicit notifications."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_namespace',ROOT/'scripts/verify-staged-hp-edge.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
g=v.g;s=v.s;N=v.N;B=v.B;E=v.E
def fixtures():
    for case in ('crossing-does-not-emit-named-event','named-event-does-not-cross-hp','explicit-ally-event-retains-name'):
        b=s.v.body(2);b['_debug_hp_events']=True;b['enemy']['patterns']=[s.lethal(at=100)]
        extra={N[0]:[B('self witness','atk_pct',170,event='hp_below:60'),B('named witness','atk_pct',70,event='event:hp_below:60')]}
        if case.startswith('crossing'):extra[N[0]].append(E('reduce hp','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1))
        else:
            name='ally_hp_below:60' if case.startswith('explicit') else 'hp_below:60'
            extra[N[0]].append(B(name,'',event='every:0.2s',max_trigger=1,event_scope='recipients'))
            if case.startswith('explicit'):extra[N[0]].append(B('ally named witness','atk_pct',90,event='event:ally_hp_below:60'))
        yield case,b,extra
def compare(device,name,b,extra,backend):
    acts=[];on_activate=v.BuffManager._activate
    def activate(self,eff,caster,t,*args,**kwargs):
        if 'witness' in eff.get('name',''):acts.append(eff['name'])
        return on_activate(self,eff,caster,t,*args,**kwargs)
    with patch.object(v.BuffManager,'_activate',activate):r=s.compare(device,name,b,extra,backend)
    expected=['self witness'] if name.startswith('crossing') else ['ally named witness'] if name.startswith('explicit') else ['named witness']
    r['checks']['independent_namespace_positive_control']=acts==expected;r['cpu_activations']=acts;r['passed']=all(r['checks'].values());print(json.dumps(dict(name=name,passed=r['passed'],cpu_activations=acts)),flush=True);return r
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],default='native');ap.add_argument('--output',default='research/detail-hp-edge-namespace-native.json');args=ap.parse_args()
    files=['scripts/verify-staged-hp-edge-namespace.py','scripts/verify-staged-hp-edge.py','scripts/staged-hp-edge-runtime.py','scripts/verify-survival-detail.py','app/survival_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']+['research/staging/v35/app/'+p for p in (('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json') if args.backend=='ptx' else ('detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'))]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};rows=[];device=s.v.v.v.Cuda()
    try:
        for name,b,extra in fixtures():
            try:r=compare(device,name,b,extra,args.backend)
            except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
            rows.append(r)
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(x['passed'] for x in rows),stage_only=True,objective_complete=False,cases=rows,source_sha256=hashes)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
