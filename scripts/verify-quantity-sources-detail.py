"""Quantity sources: independent stimuli, then existing whole-squad comparator."""
import argparse,copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from gpu_selector import Cuda
from calculator.buff_manager import BuffManager
import detail_gpu as g
spec=importlib.util.spec_from_file_location('quantity_oracles',ROOT/'scripts/verify-gauge-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.effect;N=['앨리스','리타','크라운','모더니아','N102']

def characters(charge=False):
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(a.META[n])) for n in N]
    if charge:
        chars[0]['charge_time_frames']=0
        chars[0]['_weapon'].update(damage_coeff=100,max_ammo=6,full_charge_mult=100,charge_time=0)
    return chars

def quantities(device,backend):
    rows=[];stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in N}
    chars=characters();base=chars[0]['_weapon']['max_ammo'];other=chars[1]['_weapon']['max_ammo']
    assert base==6  # 25% of six is 1.5 rounds, rounded to two before adding flat capacity.
    effects=[E('capacity scale','buff','charge_dmg_pct',2,'all_allies',scaling='max_ammo_count'),
        E('flat capacity','buff','max_ammo_flat',3,event='on_attack'),
        E('percent capacity','buff','max_ammo_pct',25,event='burst_cast',duration=.1),
        E('remove capacity','instant','remove_named_buff',0,event='full_burst_start',target_effect='flat capacity'),
        E('temporary weapon','weapon_change','',0,event='full_burst_end',weapon_type='MG',damage_coeff={'10':100},max_ammo=7,duration=.1)]
    program=g.compile_effects(chars,[(e,N[0]) for e in effects]);script=[[0,0,0,0,0,-1,0,0]]
    checks=[(0,None,0,12),(0,None,1,2*other),(.1,7,0,18),(.2,3,0,22),(.31,None,0,18),(.4,1,0,12),(.5,2,0,14),(.61,None,0,12)]
    for i,(t,event,who,expected) in enumerate(checks):
        if event is not None:script.append([t,0,event,0,0,-1,0,0])
        script.append([t,2,103,who,8,i,0,0])
    if device:
        result=g.run(device,[program],script,[[0,0]],[stats],module_backend=backend);actual=[q[0] for q in result['queries'][0]]
        assert actual==[q[3] for q in checks],('live capacity',actual,checks)
    rows.append(dict(name='live-recipient-capacity-rounding-expiry-mode',passed=True,expected=[q[3] for q in checks]))
    # An isolated CPU manager confirms query-time sampling and recursive query suppression.
    class BM(BuffManager):
        def _register_all(self):self._effects=copy.deepcopy([(effects[0],N[0])]);self._build_notify_index()
    manager=BM(chars,state=dict(base_stats=stats,full_burst=False,enemy={},hp_pct={n:100 for n in N}))
    capacities={n:7+i for i,n in enumerate(N)}
    def provider(owner,t):
        assert manager._scale_by_max_ammo(2,owner,t) is None
        return capacities[owner]
    manager.max_ammo_provider=provider;manager.notify('battle_start',0,N[0])
    assert manager.get_buffs(N[0],'target',0)['charge_dmg_pct']==14
    capacities[N[0]]=11;manager._bump_value_version()
    assert manager.get_buffs(N[0],'target',.1)['charge_dmg_pct']==22
    rows.append(dict(name='cpu-live-capacity-and-recursion-scope',passed=True))
    for name in ('missing','fractional','nested','multipliers','bullet-delay'):
        chars=characters(True);weapon=g.weapon_rows(chars,stats)[:g.CW]
        assert weapon[8]==3 and weapon[16]==0 and weapon[19]==100
        es=[E('no critical','buff','crit_rate',-15,'all_allies')]
        fixed=lambda label,pct,event='full_charge_hit':E(label,'damage','dealt_fixed_damage',pct,'target_body',event=event)
        es.append(fixed('root fixed',50));enemy=[0,0];expected=0 if name=='missing' else 1500
        if name=='fractional':es[-1]['fixed_value']=33.37;expected=1333
        if name=='nested':
            es += [E('parent','damage','damage',20,'target',event='full_charge_hit'),fixed('nested cannot inherit',1000,'hit_count:parent:1'),E('child power','buff','atk_pct',100,event='hit_count:parent:1'),fixed('restored root',25)]
            expected=1950
        if name=='multipliers':
            es += [E('attack power','buff','atk_pct',100),E('received damage','buff','received_dmg_pct',100,'target')];enemy=[500,0];expected=4500
        if name=='bullet-delay':
            es += [E('next shot capacity','buff','charge_dmg_pct',2,event='full_charge_fire',scaling='max_ammo_count',duration_bullets=1)];expected=3180
        program=g.compile_effects(chars,[(e,N[0]) for e in es]);script=[[0,0,0,0,0,-1,0,0]]
        script.append([.1,0 if name=='missing' else 3,12 if name=='missing' else 0,0,0,-1,0,0])
        if name=='bullet-delay':script.append([1,3,0,0,0,-1,0,0])
        script.append([1,2,0,0,-1,0,0,0])
        actual=None
        if device:
            result=g.run(device,[program],script,[enemy],[stats],module_backend=backend);actual=result['queries'][0][0][38]
            assert actual==expected,(name,expected,actual)
        rows.append(dict(name='captured-parent-'+name,passed=True,expected=expected,actual=actual))
    for row in rows:print(json.dumps(dict(name=row['name'],passed=True)),flush=True)
    return rows

def squads(device,backend):
    rows=[]
    for label,names in [('raw-quantity-sources',['에밀리아','리타','크라운','앨리스','모더니아']),('raw-capacity-support',['리타','크라운','에밀리아','프리바티','누아르']),('raw-parent-packets-sources-counters',['N102','크라운','에밀리아','일레그 : 붐 앤 쇼크','아인'])]:
        body=body_for(names,45,True);body.update(seed=12345,burst_gauge_mode='fixed')
        if 'counters' in label:body['enemy']['code']='작열'
        compiled=a.evaluate({**body,'_compile_gpu_detail':True})
        assert any(r[10]==-4 for r in compiled['program']['effects']) and any(r[1]==36 for r in compiled['program']['effects'])
        row=v.full.compare(device,label,body,module_backend=backend);assert row['passed'],row;rows.append(row)
        print(json.dumps(dict(name=label,passed=True,cpu=row['cpu_total'],gpu=row['gpu_total'])),flush=True)
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};started=time.perf_counter();device=None if args.cpu_preflight else Cuda()
    try:rows=quantities(device,args.backend)+([] if args.cpu_preflight else squads(device,args.backend))
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cases=rows,source_stable=True,source_sha256=before,cpu_trace_used_as_gpu_input=False,seconds=time.perf_counter()-started,scope='Independent live-ammunition and parent-damage quantities, plus raw whole-squad comparisons. Not independent game-frame verification.')
    suffix='cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT/f'research/quantity-sources-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
