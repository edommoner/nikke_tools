"""Shared command quantities before autonomous manual-reload mode production."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from test_weapon_mode_specs import effect,mode,chars,NAMES,manager
from gpu_selector import Cuda
import detail_gpu as g

def modes(device,backend):
    rows=[];bs={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in NAMES}
    for reentrant in (False,True):
        es=[mode(),effect('ended','buff','atk_pct',1,'event:state_end:mode',duration=-1,max_stack=100)]
        if reentrant:es += [mode('mode','event:state_end:mode',max_trigger=1)]
        else:es += [mode('other','burst_cast',damage_coeff=125)]
        steps=[(0,7,1,0),(.1,7,1,1),(.41,None,0,2)] if reentrant else [(0,7,1,0),(.1,3,1,0),(.2,7,1,0),(.25,7,0,1),(.3,7,1,1),(.61,None,0,2)]
        bm=manager(es);p=g.compile_effects(chars(),[(e,NAMES[0]) for e in es]);script=[];expected=[];cpu=[]
        for index,(at,event,active,ended) in enumerate(steps):
            bm.tick(at)
            if event is not None:bm.notify('on_attack' if event==7 else 'burst_cast',at,NAMES[0])
            snapshot=[int(bool(bm.weapon_change_name(NAMES[0]))),bm.get_buffs(NAMES[0],'__enemy__',at).get('atk_pct',0)]
            assert snapshot==[active,ended],(reentrant,at,snapshot);cpu.append(snapshot);expected.append([active,ended])
            script += [[at,0 if event is not None else 1,event or 0,0,0,-1,0,0],[at,2,0,0,-1,index,0,0]]
        result=g.run(device,[p],script,[[0,0]],[bs],module_backend=backend);actual=[[q[35],q[0]] for q in result['queries'][0]]
        assert actual==expected,(reentrant,actual,expected)
        rows.append(dict(name='toggle-reentrant-end' if reentrant else 'toggle-replace-and-expire',passed=True,cpu=cpu,gpu=actual,independent_expected=expected))
    # The two equivalent-ammo sources run synchronously. A child consumes its
    # own notice remainder while the parent's remainder remains intact.
    es=[effect('outer','instant','squad_ammo_consume_as',8.9),effect('child','instant','squad_ammo_consume_as',3,'squad_ammo_consume:4',max_trigger=1),effect('all notices','buff','atk_pct',1,'squad_ammo_consume:1',duration=-1,max_stack=100),effect('every three','buff','atk_pct',1,'squad_ammo_consume:3',duration=-1,max_stack=100)]
    owners=[0,2,3,1];bm=manager(es,owners);p=g.compile_effects(chars(),[(e,NAMES[o]) for e,o in zip(es,owners)])
    bm.notify('on_attack',0,NAMES[0]);bm.notify('squad_ammo_consume',0,NAMES[0])
    cpu=[bm.get_buffs(NAMES[i],'__enemy__',0).get('atk_pct',0) for i in (3,1)];assert cpu==[10,3]
    script=[[0,0,7,0,0,-1,0,0],[0,0,26,0,0,-1,0,0],[0,2,103,3,0,0,0,0],[0,2,103,1,0,1,0,0],[0,2,108,0,0,2,0,0]]
    result=g.run(device,[p],script,[[0,0]],[bs],module_backend=backend);q=result['queries'][0];actual=[q[0][0],q[1][0]]
    assert actual==[10,3] and q[2][10]==120,(actual,q[2][10])
    rows.append(dict(name='nested-notice-remainders-without-real-ammo-consumption',passed=True,cpu=cpu,gpu=actual,independent_expected=[10,3],unchanged_real_ammo=120))
    # Exercise real GPU weapon execution inside a declared mode, then turn it
    # off. This is authored input, not a CPU-generated shot or buff trace.
    es=[effect('no critical','buff','crit_rate',-15,'battle_start',target='all_allies',duration=-1),mode(event='burst_cast',duration=-1,charge_time=0,full_charge_mult=100),
        effect('equivalent shot','instant','squad_ammo_consume_as',40,'full_charge_fire'),effect('tenth notice','buff','atk_pct',1,'squad_ammo_consume:10',duration=-1,max_stack=100)]
    p=g.compile_effects(chars(),[(e,NAMES[0]) for e in es])
    script=[[0,0,0,0,0,-1,0,0],[.1,0,3,0,0,-1,0,0],[.1,3,0,0,0,-1,0,0],[.1,2,0,0,-1,0,0,0],[.2,0,3,0,0,-1,0,0],[.2,2,0,0,-1,1,0,0]]
    result=g.run(device,[p],script,[[0,0]],[bs],module_backend=backend);q=result['queries'][0]
    # One real round plus39 equivalent notices; four threshold10 activations.
    # The current shot was frozen before those child buffs, so stays1000.
    actual=[[r[35],r[38],r[43],r[0],r[44]] for r in q];expected=[[1,1000,1,4,5],[0,1000,1,4,5]];assert actual==expected,(actual,expected)
    rows.append(dict(name='real-weapon-shot-between-toggle-commands',passed=True,gpu=actual,independent_expected=expected))
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'tests/test_weapon_mode_specs.py',ROOT/'app/detail_effects.cu']
    files += [ROOT/'app'/name for name in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};start=time.perf_counter();device=Cuda()
    try:rows=modes(device,args.backend)
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cases=rows,source_sha256=before,source_stable=True,seconds=time.perf_counter()-start,cpu_trace_used_as_gpu_input=False,autonomous_manual_reload_input_connected=False,character_admission_changed=False)
    (ROOT/f'research/mode-commands-{args.backend}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,cases=len(rows))))

if __name__=='__main__':main()
