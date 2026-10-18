"""Typed transport witnesses plus independently simulated existing squad paths."""
import argparse,hashlib,importlib.util,json,math,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from gpu_selector import Cuda
from calculator.buff_manager import BuffManager
from effect_runtime import state
from impact_specs import ActorHandle,Impact,ImpactTrace,impact_command
from resource_frame_capture import FrameCapture
import detail_gpu as g
spec=importlib.util.spec_from_file_location('impact_gauge_oracle',ROOT/'scripts/verify-gauge-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def quantities(device,backend):
    names=v.NAMES;program=g.compile_effects([{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':a.META[n]} for n in names],[])
    stats={n:dict(atk=1000,hp=10000,**{'def':100}) for n in names}
    script=[];expected=[];counts=[0]*24;outcomes=[0]*3;credit=damage=0
    for kind in range(6):
        for family in range(4):
            for outcome in range(3):
                j=len(expected);hit=10+j if outcome==2 else 0;count=.25+family if outcome else 0
                # Distinct generations, IDs and credits are authored inputs, not CPU battle output.
                packet=Impact(names[j%5],ActorHandle(kind,100+kind,7+j),family,outcome,hit,count,42+j)
                script.append(impact_command(j/10,packet,names));script.append([j/10,2,126,0,0,j,0,0])
                counts[kind*4+family]+=1;outcomes[outcome]+=1;credit+=count;damage+=hit
                row=[0.0]*48;row[0]=j+1;row[1:25]=counts;row[25:27]=[credit,damage];row[40:43]=outcomes
                row[27:37]=[kind,100+kind,7+j,family,outcome,j%5,hit,count,42+j,j/10];expected.append(row)
    result=g.run(device,[program],script,[[0,0]],[stats],module_backend=backend)
    assert result['queries'][0]==expected
    assert result['totals'][0]==[0]*5,'Diagnostic transport must not manufacture battle damage'
    return dict(name='typed-wire-all-actors-families-outcomes',passed=True,packets=len(expected),damage_independent_of_credit=True)


def scenarios():
    body=body_for(v.NAMES,8,True);body.update(seed=12345,burst_gauge_mode='fixed',_debug_impact_frames=True)
    body['enemy']['core_px']=10000
    yield 'existing-grown-squad-all-core',body,None
    names=['슈가']+v.NAMES[:4]
    body=body_for(names,8,True);body.update(seed=12345,burst_gauge_mode='fixed',_debug_impact_frames=True)
    body['enemy']['core_px']=10000
    body['enemy']['parts']=[dict(name='left',hp=0,reach=1),dict(name='right',hp=7000000,reach=1)]
    E=v.effect
    effects={names[0]:[
        E('piercing weapons','buff','pierce_enabled',1,'all_allies'),
        E('damage over time','damage','dot_damage',50,'target',tick_interval=.25,duration=7,hits_parts=True),
        E('sequential landing','damage','sequential_damage:3',150,'target',event='burst_cast',land_in_full_burst=True,hits_parts=True),
        E('named direct hit','damage','damage',75,'target',event='on_attack',hits_parts=True),
        E('drain','instant','current_hp_reduce',50),E('heal from landed hits','buff','lifesteal_pct',25)]}
    yield 'shotgun-skill-dot-body-parts-and-recovery',body,effects


def squads(device,backend,cpu_only=False):
    rows=[]
    for name,body,effects in scenarios():
        names=body['squad'];captured=[];original=BuffManager.__init__
        def init(manager,*args,**kwargs):
            original(manager,*args,**kwargs)
            if 'hp' in manager.state:state(manager).impact_trace=ImpactTrace();captured.append(manager)
        def project(manager,t,observer):
            return [dict(time=t,fields=state(manager).impact_trace.fields(names))]
        from contextlib import nullcontext
        with (v.custom_effects(effects) if effects is not None else nullcontext()),patch.object(BuffManager,'__init__',init),FrameCapture(v.full,project) as witness:
            from calculator import timeline
            code=timeline.simulate.__code__;previous=sys.gettrace()
            def trace(frame,event,arg):return trace if frame.f_code is code else None
            try:
                sys.settrace(trace)
                if cpu_only:
                    cpu=a.evaluate(body);row=dict(name=name,passed=True,cpu_total=cpu['total_damage'])
                else:row=v.full.compare(device,name,body,module_backend=backend)
            finally:sys.settrace(previous)
        samples=witness.samples+witness.final_samples
        assert samples and captured and samples[-1]['fields'][0]>0,(name,len(samples))
        final=samples[-1]['fields']
        if effects is not None:
            assert all(final[1+kind*4+family]>0 for kind in (0,1) for family in (0,1,2)),final
            assert final[25]==final[0],'Each supported landed packet has one hit credit'
        if not cpu_only:
            gpu=witness.gpu['_impact_frames'];assert len(samples)==len(gpu),(len(samples),len(gpu))
            for i,(left,right) in enumerate(zip(samples,gpu)):
                assert math.isclose(left['time'],right['time'],abs_tol=1e-12)
                for field,(cpu_value,gpu_value) in enumerate(zip(left['fields'],right['fields'])):
                    assert math.isclose(cpu_value,gpu_value,rel_tol=1e-12,abs_tol=1e-6),(name,i,field,cpu_value,gpu_value)
            assert row['passed'],row
        row.update(impact_frames=len(samples),impact_count=final[0],impact_credit=final[25],typed_counts=final[1:25],last_impact=final[27:37])
        rows.append(row);print(json.dumps(dict(name=name,passed=True,frames=len(samples),packets=final[0])),flush=True)
    return rows


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('native','ptx'),default='native');parser.add_argument('--cpu-preflight',action='store_true');args=parser.parse_args()
    files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'app').glob('*.py')}|{'app/detail_effects.cu','scripts/verify-typed-impacts-detail.py','scripts/resource_frame_capture.py','scripts/verify-gauge-detail.py','scripts/verify-extended-detail.py','data/engine-effect-overrides.json'})
    if not args.cpu_preflight:files+=['app/detail_effects-sm86.cubin','app/detail_effects-sm86.json'] if args.backend=='native' else ['app/detail_effects.ptx','app/detail_effects-build.json']
    def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    before=hashes();device=None if args.cpu_preflight else Cuda()
    try:rows=([] if args.cpu_preflight else [quantities(device,args.backend)])+squads(device,args.backend,args.cpu_preflight)
    finally:
        if device:device.close()
    assert before==hashes()
    report=dict(passed=all(r['passed'] for r in rows),cases=rows,source_sha256=before,source_stable=True,cpu_trace_used_as_gpu_input=False,
        scope='Typed impact transport and supported body/part landing migration. Target counters, enemy projectile/shield world routing and death completion remain unfinished.')
    suffix='cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT/f'research/typed-impacts-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
