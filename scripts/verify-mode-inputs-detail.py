"""GPU decides reloads from its state; no CPU-selected times feed its inputs."""
import argparse,copy,hashlib,importlib.util,json,math,sys,time
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from test_weapon_mode_specs import effect,mode,NAMES
from calculator.buff_manager import BuffManager
from calculator.timeline import CharState
from gpu_selector import Cuda
import detail_gpu as g
spec=importlib.util.spec_from_file_location('mode_input_legacy',ROOT/'scripts/verify-modes-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def cases():
    for flag,conditional,ready in ((True,True,True),(False,True,True),(True,True,False),(True,False,True)):
        body=body_for(NAMES,2,True);body.update(weapon_mode_swap=flag,seed=12345,burst_gauge_mode='fixed')
        es=[effect('reload duration','buff','reload_time_fixed',.5,'battle_start',duration=-1),
            mode(event='event:full_reload',duration=.6,charge_time=.2,full_charge_mult=100),
            effect('off core','buff','core_dmg_pct',10,'battle_start',duration=-1),
            effect('on core','buff','core_dmg_pct',10,'event:mode',duration=-1),
            effect('clear on core','instant','remove_named_buff',0,'event:state_end:mode',target_effect='on core'),
            effect('equivalent','instant','squad_ammo_consume_as',40,'full_charge_fire')]
        es[1]['trigger']['condition']=['self_state:ready'] if conditional else []
        if ready:es.insert(0,effect('ready','buff','',0,'battle_start',duration=-1))
        yield 'conditional-mode-'+''.join(str(int(i)) for i in (flag,conditional,ready)),body,{NAMES[0]:es},NAMES[0],bool(flag and conditional and ready),10
    name='신데렐라 : 크리스탈 웨이브'
    for flag,gauge,parts in ((True,'fixed',False),(True,'accumulate',False),(False,'fixed',False),(True,'fixed',True)):
        body=body_for([name,'리타','크라운','앨리스','모더니아'],45,True);body.update(weapon_mode_swap=flag,seed=12345,burst_gauge_mode=gauge)
        if parts:body['enemy']['parts']=[dict(name='left',hp=0,reach=1),dict(name='right',hp=0,reach=3)]
        yield 'raw-mode-'+str(int(flag))+'-'+gauge+('-parts' if parts else ''),body,{},name,flag,0

def compare(device,backend,label,body,custom,subject,expected_active,off_core):
    body={**body,'_debug_scalar_query':{'who':body['squad'].index(subject),'key':7},'_debug_weapon_frames':{'who':body['squad'].index(subject)}}
    frames=[];counts=dict(mode_entries=0,full_charge_fire=0,ammo_notices=0,mode_shots=0);original_tick=CharState.tick;original_notify=BuffManager.notify;original_mode=CharState._tick_weapon_change
    def tick(self,t,bm,*args,**kwargs):
        result=original_tick(self,t,bm,*args,**kwargs)
        if self.name==subject:frames.append(dict(time=t,active=bool(bm.get_weapon_change(subject)),core=bm.get_buffs(subject,'__enemy__',t).get('core_dmg_pct',0),ammo=self.ammo,reloading_until=self.reloading_until,phase={'ready':0,'charging':1,'post_delay':2}[self._charge_phase]))
        return result
    def notify(self,event,t,caster,*args,**kwargs):
        if caster==subject:
            counts['full_charge_fire']+=event=='full_charge_fire';counts['ammo_notices']+=event=='squad_ammo_consume'
        return original_notify(self,event,t,caster,*args,**kwargs)
    def mode_tick(self,t,*args,**kwargs):
        before=self._wc_shots;result=original_mode(self,t,*args,**kwargs)
        if self.name==subject:counts['mode_shots']+=max(0,self._wc_shots-before)
        return result
    cpu_result={};original_evaluate=a.evaluate
    def evaluate(request):
        result=original_evaluate(request)
        if not request.get('_compile_gpu_detail'):cpu_result.update(result)
        return result
    with (v.p.custom_effects(custom) if custom else nullcontext()):
        compiled=a.evaluate({**body,'_compile_gpu_detail':True});gpu=g.evaluate_full(device,compiled,module_backend=backend)
        with patch.object(CharState,'tick',tick),patch.object(BuffManager,'notify',notify),patch.object(CharState,'_tick_weapon_change',mode_tick),patch.object(a,'evaluate',evaluate):
            row=v.p.full.compare(device,label,body,module_backend=backend,gpu_result=gpu)
    assert row['passed'],row
    if body['enemy'].get('parts'):assert cpu_result['parts_state']==gpu['parts_state'],(label,cpu_result['parts_state'],gpu['parts_state'])
    scalar=gpu['_scalar_frames'];weapons=gpu['_weapon_frames'];assert len(frames)==len(scalar)==len(weapons),(label,len(frames),len(scalar),len(weapons))
    mismatches=[];gpu_mode_shots=0;previous_shots=0
    for cpu,s,w in zip(frames,scalar,weapons):
        for key,actual,expected in [('time',s['time'],cpu['time']),('core',s['value'],cpu['core']),('ammo',w['ammo'],cpu['ammo']),('reload',w['reloading_until'],cpu['reloading_until'])]:
            if not math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-8):mismatches.append(dict(time=cpu['time'],key=key,cpu=expected,gpu=actual))
        if cpu['active'] and w['phase']!=cpu['phase']:mismatches.append(dict(time=cpu['time'],key='phase',cpu=cpu['phase'],gpu=w['phase']))
        gpu_active=s['value']>off_core if custom else s['value']==0
        if gpu_active:gpu_mode_shots+=w['shots']-previous_shots
        previous_shots=w['shots']
    assert not mismatches,(label,mismatches[:12])
    active=any(f['active'] for f in frames);assert active==expected_active,(label,active,counts)
    assert gpu_mode_shots==counts['mode_shots'],(label,gpu_mode_shots,counts)
    if expected_active:assert counts['mode_shots']>0 and counts['ammo_notices']>=40*counts['full_charge_fire'],(label,counts)
    if label=='conditional-mode-111':assert math.isclose(next(f['time'] for f in frames if f['active']),31/60,abs_tol=1e-9)
    row.update(passed=True,frame_witnesses=len(frames),cpu_mode_shots=counts['mode_shots'],gpu_mode_shots=gpu_mode_shots,mode_expected=expected_active,cpu_notices=counts,raw_skills_retained=not bool(custom),weapon_mode_swap=body['weapon_mode_swap'],parts_state=gpu.get('parts_state'),workspace_bytes=gpu['compute']['workspace_bytes'])
    print(json.dumps(dict(name=label,passed=True,cpu=row['cpu_total'],gpu=row['gpu_total'],mode_shots=gpu_mode_shots,frames=len(frames))),flush=True);return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');args=ap.parse_args()
    # Record the execution dependencies rather than every unrelated verifier.
    # Editing an API smoke test must not invalidate a numerical proof.
    files=list((ROOT/'app').glob('*.py'))+[ROOT/'scripts'/name for name in ('verify-mode-inputs-detail.py','verify-modes-detail.py','verify-periodic-detail.py','verify-extended-detail.py','detail_coverage.py','target_counter_cases.py')]
    files += [ROOT/'tests'/name for name in ('test_mode_input_policy.py','test_weapon_mode_specs.py','test_target_counter_runtime.py')]+[ROOT/'app/detail_effects.cu']
    files += list((ROOT/'research/upstream/nikke-calc-master/calculator').glob('*.py'))+list((ROOT/'research/upstream/nikke-calc-master/runner').glob('*.py'))
    files += list((ROOT/'research/upstream/nikke-calc-master/data').rglob('*.json'))
    files += [ROOT/'app'/name for name in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};start=time.perf_counter();device=Cuda()
    try:rows=[compare(device,args.backend,*case) for case in cases()]
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cases=rows,source_sha256=before,source_stable=True,cpu_trace_used_as_gpu_input=False,seconds=time.perf_counter()-start)
    (ROOT/f'research/mode-inputs-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
