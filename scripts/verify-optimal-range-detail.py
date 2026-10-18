"""Dynamic range primitives and independent five-member CPU/GPU battles."""
import argparse,copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=module('optimal_periodic','scripts/verify-periodic-detail.py')
raw=module('optimal_raw','scripts/verify-cleanse-detail.py')
oracle=module('optimal_primitive','scripts/verify-detail.py')
from calculator import buff_manager,timeline
from calculator.buff_manager import optimal_range_of,in_optimal_range
from detail_gpu import compile_effects,run,evaluate_full
from gpu_selector import Cuda
from gpu_service import resolve_verification
E=p.effect


def primitives(device,backend):
    refs=json.loads((ROOT/'research/detail-range-geometry-cpu-references.json').read_text(encoding='utf-8'))
    for f,h in refs['source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
    cases=list(refs['optimal'])
    # Closed interval with the CPU's epsilon on both boundaries, including
    # negative debuffs, >100% extension and the RL [0,0] edge.
    for name,weapon in [('앨리스','SR'),('하란','SR'),('앨리스','AR'),('N102','RL')]:
        lo,hi=optimal_range_of(name,weapon)
        for distance in [lo-2e-9,lo-.5e-9,lo,hi,hi+.5e-9,hi+2e-9]:
            for low,high in [(-50,0),(0,-50),(150,100),(0,0)]:
                enemy={'distance':distance};buffs={'optimal_range_min_pct':low,'optimal_range_max_pct':high}
                cases.append(dict(input=dict(name=name,weapon_type=weapon,enemy=enemy,buffs=buffs),base_range=[lo,hi],expected=in_optimal_range(enemy,name,weapon,buffs)))
    script=[[0,0,0,0,0,-1,0,0],[0,2,113,0,0,0,0,0]]
    errors=[]
    for start in range(0,len(cases),16):
        group=cases[start:start+16];programs=[];stats=[]
        for ref in group:
            value=ref['input'];name=value['name'];names=[name]+[n for n in p.NAMES if n!=name][:4]
            chars=oracle.characters(names)
            for char in chars:
                lo,hi=optimal_range_of(char['name'],char['_weapon']['weapon_type']);char['_detail_range']=[lo,hi,None]
            chars[0]['_detail_range']=[*ref['base_range'],value['enemy'].get('distance')]
            chars[0]['_optimal']=value['weapon_type'] in value['enemy'].get('optimal_range_weapons',[])
            effects=[(E('min range','buff','optimal_range_min',value['buffs']['optimal_range_min_pct']),name),
                     (E('max range','buff','optimal_range_max_pct',value['buffs']['optimal_range_max_pct']),name)]
            programs.append(compile_effects(chars,effects));stats.append({n:{'atk':10000,'def':1000,'hp':100000} for n in names})
        result=run(device,programs,script,[[0,0]]*len(group),stats,module_backend=backend)
        for j,ref in enumerate(group):
            actual=bool(result['queries'][j][0][0])
            if actual!=ref['expected']:errors.append(dict(index=start+j,input=ref['input'],expected=ref['expected'],actual=actual))
    row=dict(kind='primitives',backend=backend,count=len(cases),passed=not errors,errors=errors)
    print(json.dumps(row,ensure_ascii=True),flush=True);return row


def scenarios():
    alice=p.NAMES[2];liter=p.NAMES[0]
    gate=E('optimal gated attack','buff','atk_pct',37,event='on_attack',condition=['optimal_range'],duration=.4)
    yield 'min-expiry-and-gate',alice,30,[E('nearer','buff','optimal_range_min',50,event='every:2s',duration=1.5),gate],True
    yield 'max-expiry-and-gate',liter,40,[E('farther','buff','optimal_range_max_pct',100,event='every:2s',duration=1.5),gate],True
    yield 'negative-min-and-gate',alice,50,[E('further minimum','buff','optimal_range_min',-50,event='every:2s',duration=1.5),gate],True
    yield 'negative-max-and-gate',alice,80,[E('closer maximum','buff','optimal_range_max_pct',-50,event='every:2s',duration=1.5),gate],True
    yield 'stacked-extension',alice,30,[E('nearer stack','buff','optimal_range_min',20,event='full_charge_fire',max_stack=5,duration=5),gate],True
    yield 'one-bullet-extension',alice,30,[E('nearer bullet','buff','optimal_range_min',100,event='full_charge',duration_bullets=1),gate],False
    yield 'team-range-recipient-order',alice,30,[E('team range','buff','optimal_range_min',50,'all_allies',event='every:2s',duration=1.5),gate],True
    yield 'fullburst-runtime-range',alice,30,[E('full burst range','buff','optimal_range_min',100,event='passive',condition=['during_full_burst']),gate],True
    mode={'source':'스킬3','name':'authored AR mode','type':'weapon_change','target':'self','weapon_type':'AR','max_ammo':-1,'damage_coeff':{'10':251},'duration':3,'trigger':{'timing':['burst_cast'],'condition':[]}}
    yield 'weapon-mode-uses-own-interval-predicate-uses-innate',alice,30,[mode,gate],False
    yield 'weapon-mode-live-extension',alice,60,[mode,E('farther mode','buff','optimal_range_max_pct',100,event='burst_cast',duration=2),gate],True
    # Normal-attack-formula skill damage must use the same dynamic interval.
    yield 'normal-formula-skill',alice,30,[E('nearer','buff','optimal_range_min',100,event='every:2s',duration=.8),E('normal skill','damage','damage',250,'target',event='every:0.5s',damage_formula='normal_attack'),gate],True


def compare(device,label,body,backend,effects=None,raw_skills=False,require_flip=False):
    context=raw.injected_effects(effects or {}) if raw_skills else p.custom_effects(effects or {})
    decisions=[];original=in_optimal_range
    def observe(enemy,name,weapon,buffs):
        answer=original(enemy,name,weapon,buffs)
        decisions.append(dict(name=name,weapon=weapon,answer=answer,min=buffs.get('optimal_range_min_pct',0),max=buffs.get('optimal_range_max_pct',0)))
        return answer
    with context:
        compiled=p.a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend)
        with patch.object(timeline,'in_optimal_range',observe),patch.object(buff_manager,'in_optimal_range',observe):cpu=p.a.evaluate(body)
        rng=list(random.getstate()[1])
    resolved=resolve_verification(gpu,cpu);checks=resolved['compute']['cpu_verification'].copy()
    checks.update(actual_gpu=resolved['compute']['backend']=='cuda_detail',final_random_state=rng==gpu['_random_state'],nonzero_damage=cpu['total_damage']>0)
    subjects=[d for d in decisions if d['name']==body.get('_range_subject',body['squad'][0])]
    changed=[d for d in subjects if d['min'] or d['max']]
    if label!='weapon-mode-uses-own-interval-predicate-uses-innate':checks['live_range_buff_exercised']=bool(changed)
    if require_flip:
        checks['range_decision_changed']={d['answer'] for d in subjects}=={False,True}
    row=dict(kind='battle',name=label,backend=backend,passed=all(checks.values()),checks=checks,raw_skills_retained=raw_skills,
             cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],mode=body['burst_gauge_mode'],distance=body['enemy']['distance'],
             observed_range_values=[list(x) for x in sorted({(d['weapon'],d['answer'],d['min'],d['max']) for d in subjects})])
    if not row['passed']:row.update(cpu_members=cpu['members'],gpu_members=gpu['members'],cpu_bursts=cpu['burst_timeline'],gpu_bursts=gpu['burst_timeline'])
    print(json.dumps(row,ensure_ascii=True),flush=True);return row


def verify(device,backend):
    rows=[primitives(device,backend)]
    for label,subject,distance,effects,flip in scenarios():
        for mode in ('fixed','accumulate'):
            body=p.body_for(p.NAMES,14,True);body.update(seed=12345,burst_policy='rules',burst_gauge_mode=mode,_debug_random_state=True,_range_subject=subject)
            body['enemy'].update(distance=distance,core_px=0)
            rows.append(compare(device,label,body,backend,{subject:effects},require_flip=flip))
    for subject,distance in [('에이드 : 에이전트 바니',30),('레오나',28)]:
        names=[subject,'리타','크라운','앨리스','모더니아']
        if subject=='레오나':names=[subject,'리타','슈가','앨리스','모더니아']
        for mode in ('fixed','accumulate'):
            for core in (0,50):
                body=p.body_for(names,60,True);body.update(seed=12345,burst_policy='rules',shooting_policy='character',burst_gauge_mode=mode,_debug_random_state=True)
                body['enemy'].update(distance=distance,core_px=core)
                rows.append(compare(device,'raw-'+subject,body,backend,raw_skills=True,require_flip=True))
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['native','ptx','both'],default='both');args=parser.parse_args()
    files=['scripts/verify-optimal-range-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    d=Cuda()
    try:rows=[r for b in (('native','ptx') if args.backend=='both' else (args.backend,)) for r in verify(d,b)]
    finally:d.close()
    assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'Sources changed during verification'
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),objective_complete=False,cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,scope='Dynamic optimal distance only. Live range geometry, parts and destruction remain unimplemented.')
    (ROOT/'research/detail-optimal-range-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
