"""Resource-associated markers reuse the existing carrier and gauge interpreter."""
import argparse,copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
from gpu_selector import Cuda
import detail_gpu as g
spec=importlib.util.spec_from_file_location('marker_oracles',ROOT/'scripts/verify-gauge-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.effect;N=v.NAMES

def primitive(device,backend):
    effects=[]
    for who,initial in ((0,0),(1,9)):
        for e in [E('start','instant','gauge_charge',initial,gauge_id='fuel',gauge_max=100),
                  dict(type='buff',source='스킬3',name='enabled',stat='gauge_charge_enabled',gauge_id='fuel',target='self',duration=.5,trigger=dict(timing=['burst_cast'],condition=['gauge_below:fuel:100'])),
                  E('gated charge','instant','gauge_charge',2,event='on_attack',gauge_id='fuel',condition=['self_state:enabled']),
                  E('recovery','instant','gauge_charge',45,event='event:state_end:enabled',gauge_id='fuel'),
                  E('fill','instant','gauge_charge',100,event='full_burst_start',gauge_id='fuel')]:effects.append((e,N[who]))
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in N];stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in N}
    program=g.compile_effects(chars,effects)
    class BM(BuffManager):
        def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
    bm=BM(chars,state=dict(base_stats=stats,enemy={},full_burst=False,hp_pct={n:100 for n in N}));script=[];expected=[]
    actions=[(0,0,0,[0,0,0,0]),(0,0,1,[0,9,0,0]),(.05,7,0,[0,9,0,0]),(.1,3,0,[0,9,1,0]),(.2,7,0,[2,9,1,0]),(.25,7,1,[2,9,1,0]),(.3,3,0,[2,9,1,0]),(.61,7,0,[4,9,1,0]),(.7,3,1,[4,9,1,1]),(.81,None,0,[49,9,0,1]),(.9,7,0,[49,9,0,1]),(.9,7,1,[49,11,0,1]),(1.21,None,0,[49,56,0,0]),(1.3,1,0,[100,56,0,0]),(1.31,3,0,[100,56,0,0])]
    for t,event,who,want in actions:
        bm.tick(t)
        if event is not None:
            bm.notify({0:'battle_start',1:'full_burst_start',3:'burst_cast',7:'on_attack'}[event],t,N[who]);script.append([t,0,event,who,0,-1,0,0])
        bm.tick(t);got=[bm.ref_count(N[i],'fuel') or 0 for i in (0,1)]+[bm.ref_count(N[i],'enabled') or 0 for i in (0,1)]
        assert got==want,('independent CPU',t,got,want)
        for i in (0,1):script.append([t,2,102,i,program['states']['fuel'],len(expected)*4+i,0,0])
        for i in (0,1):script.append([t,2,0,i,program['states']['enabled'],len(expected)*4+2+i,0,0])
        expected.append(want)
    result=g.run(device,[program],script,[[0,0]],[stats],module_backend=backend)
    actual=[[result['queries'][0][4*i+j][0 if j<2 else 37] for j in range(4)] for i in range(len(expected))]
    assert actual==expected,('GPU marker lifecycle',actual,expected)
    return dict(name='resource-marker-owner-refresh-expiry-cap',passed=True,expected=expected,actual=actual)

def squads(device,backend):
    rows=[]
    for reordered in (False,True):
        names=['네온 : 비전 아이','리타','크라운','앨리스','모더니아']
        if reordered:names=[names[2],names[1],names[4],names[0],names[3]]
        body=body_for(names,90,True);body.update(seed=12345,burst_gauge_mode='fixed');observed=dict(bind=0,expire=0,gated_charge=0,recovery=0)
        class Observed(BuffManager):
            def _activate(self,eff,caster,t,*args,**kwargs):
                gauge=eff.get('gauge_id');before=self.state.get('gauges',{}).get(caster,{}).get(gauge,0)
                active=lambda:any(b.caster==caster and b.effect.get('stat')=='gauge_charge_enabled' for b in self._active)
                enabled=active();result=super()._activate(eff,caster,t,*args,**kwargs)
                if eff.get('stat')=='gauge_charge_enabled' and active():observed['bind']+=1
                if eff.get('stat')=='gauge_charge':
                    after=self.state.get('gauges',{}).get(caster,{}).get(gauge,0)
                    if after>before:
                        if enabled:observed['gated_charge']+=1
                        elif any(x.startswith('event:state_end:') for x in eff.get('trigger',{}).get('timing',[])):observed['recovery']+=1
                return result
            def tick(self,t):
                due=[b for b in self._active if b.effect.get('stat')=='gauge_charge_enabled' and b.expires_at<=t]
                result=super().tick(t);observed['expire']+=sum(not any(b is a for a in self._active) for b in due);return result
        from calculator import buff_manager,timeline
        with patch.object(buff_manager,'BuffManager',Observed),patch.object(timeline,'BuffManager',Observed):row=v.full.compare(device,'raw-resource-marker'+('-reordered' if reordered else ''),body,module_backend=backend)
        assert row['passed'] and all(observed.values()),(row,observed)
        row['cpu_lifecycle_witness']=observed;rows.append(row);print(json.dumps(dict(name=row['name'],passed=True,witness=observed)),flush=True)
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'app/detail_effects.cu',ROOT/'tests/test_resource_specs.py',ROOT/'data/engine-effect-overrides.json']
    files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};start=time.perf_counter();device=Cuda()
    try:rows=[primitive(device,args.backend)]+squads(device,args.backend)
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cases=rows,source_sha256=before,source_stable=True,cpu_trace_used_as_gpu_input=False,kernel_rebuilt=False,seconds=time.perf_counter()-start)
    (ROOT/f'research/resource-marker-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
