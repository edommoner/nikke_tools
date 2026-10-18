"""Same authored frame/weapon/burst/target cases for CUDA and Metal.
No CPU battle trace, shot schedule, target HP or burst state is GPU input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
import engine_worker
from timer_registry_cases import NAMES
from portable_runtime import compile_program,run_programs,PortableExecutionError


def fixtures():
    return sum((json.loads((ROOT/'tests/fixtures'/name).read_text(encoding='utf-8'))['cases'] for name in ('portable-combat.json','portable-combat-extensions.json','portable-autonomous.json','portable-triggers.json','portable-damage.json','portable-weapons.json','portable-quantities.json','portable-charge-control.json','portable-health.json','portable-hp-edges.json','portable-incoming.json','portable-capacity.json','portable-recipients.json','portable-carriers.json','portable-lazy.json')),[])


def compile_case(case):
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    return compile_program(chars,[(e,NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))],case['script'],case.get('base_atk',[1000]*5),combat=case.get('combat'),**case.get('environment',{}))


def contains(actual,expected,path=''):
    if isinstance(expected,dict):
        for k,v in expected.items():contains(actual[k],v,path+'.'+k)
    elif isinstance(expected,list):
        assert len(actual)>=len(expected),(path,len(actual),len(expected))
        for i,v in enumerate(expected):contains(actual[i],v,path+f'[{i}]')
    else:assert actual==expected,(path,actual,expected)



def verify_trigger_reference(cases):
    # An independent CPU regression is evaluated only AFTER the GPU invocation.
    # Hand-authored expectations remain the common acceptance criteria.
    import importlib.util
    spec=importlib.util.spec_from_file_location('portable_trigger_oracle',ROOT/'scripts/verify-detail.py')
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    chars=oracle.characters(NAMES)
    stats={n:dict(atk=1000,defense=0,hp=1000000) for n in NAMES}
    verified=[]
    for case in cases:
        if 'combat' in case or 'damage_reference' in case and not case.get('trigger_reference'):continue
        program=oracle.program(chars,[(e,NAMES[0]) for e in case['effects']])
        queries,_=oracle.oracle(program,case['script'],[0,0],stats)
        actual=[q[0] for q in queries];expected=[q['attack_buffs'][0] for q in case['expected_queries']]
        assert actual==expected,(case['name'],actual,expected)
        verified.append(case['name'])
    return verified



def verify_damage_reference(cases):
    from calculator.damage import calc_damage,default_hit_type
    verified=[]
    for case in cases:
        if 'damage_reference' not in case:continue
        sample=dict(case['damage_reference']);expected=sample.pop('expected')
        sample['hit_type']=default_hit_type(**sample['hit_type'])
        actual=calc_damage(**sample,expected=True)['damage']
        assert actual==expected,(case['name'],actual,expected)
        verified.append(case['name'])
    return verified



def verify_weapon_reference(cases):
    from portable_weapon_oracle import observe
    verified=[];differences=[]
    for case in cases:
        if not case.get('weapon_reference'):continue
        queries,final=observe(case)
        # The weapon oracle observes damage/weapon state; allied HP/defense
        # remain checked by GPU hand expectations and the separate health oracle.
        cpu_expected=case.get('known_cpu_difference',{}).get('expected_queries',case['expected_queries'])
        contains(queries,[{k:v for k,v in q.items() if k in ('damage','combat')} for q in cpu_expected],case['name']+'.cpu')
        if 'known_cpu_difference' in case:
            differences.append(dict(name=case['name'],reason=case['known_cpu_difference']['reason'],actual_cpu_queries=queries,expected_cpu_queries=case['known_cpu_difference']['expected_queries'],expected_gpu_queries=case['expected_queries']))
        if 'expected_final' in case:
            expected=case['expected_final'].get('weapons',[{}])[0]
            contains(final,{k:v for k,v in expected.items() if k in ('warm','last_interval')},case['name']+'.cpu.final')
        verified.append(case['name'])
    return verified,differences


def verify_health_reference(cases, results):
    from portable_health_oracle import observe
    names=[];differences=[]
    for case,result in zip(cases,results):
        if not case.get('health_reference'):continue
        actual=observe(case)
        expected=case.get('known_health_cpu_difference',{}).get('expected_queries',case['expected_queries'])
        for cpu,hand in zip(actual,expected):
            if 'attack_buffs' in hand:contains(cpu['attack_buffs'],hand['attack_buffs'],case['name']+'.cpu.attack')
            for index,values in enumerate(hand.get('allies',[])):
                contains(cpu['allies'][index],{k:v for k,v in values.items() if k!='healing'},case['name']+'.cpu.health')
        if 'known_health_cpu_difference' in case:
            differences.append(dict(name=case['name'],reason=case['known_health_cpu_difference']['reason'],actual_cpu_queries=actual,expected_cpu_queries=expected,expected_gpu_queries=case['expected_queries']))
        else:
            for gpu,cpu in zip(result['queries'],actual):
                contains(gpu['allies'],cpu['allies'],case['name']+'.gpu_vs_cpu')
                contains(gpu['attack_buffs'],cpu['attack_buffs'],case['name']+'.gpu_vs_cpu.attack')
        names.append(case['name'])
    return names,differences


def evidence_subset(result):
    return {key:result[key] for key in ('transport','source_sha256','generated_sha256',
                                       'input_sha256','output_sha256','gpu_execution_verified','backend')}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    args=parser.parse_args();path=ROOT/f'research/portable-combat-{args.backend}.json'
    path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='execution-pending'))+'\n',encoding='utf-8')
    tracked=['app/portable_runtime.py','app/portable_combat.py','app/portable_specs.py','app/portable_backend.py',
             'app/portable_trigger_specs.py','app/portable_recipient_specs.py','app/portable_damage_specs.py','scripts/portable_capacity_oracle.py','scripts/portable_health_oracle.py','scripts/portable_weapon_oracle.py','scripts/verify-detail.py','app/detail_gpu.py','app/effect_spec.py','app/impact_specs.py','app/world_condition_specs.py','scripts/verify-portable-combat.py',
             'tests/fixtures/portable-lazy.json','tests/fixtures/portable-lazy-capacity-rejection.json','tests/fixtures/portable-carriers.json','tests/fixtures/portable-recipients.json','tests/fixtures/portable-capacity.json','tests/fixtures/portable-incoming.json','tests/fixtures/portable-hp-edges.json','tests/fixtures/portable-health.json','tests/fixtures/portable-charge-control.json','tests/fixtures/portable-quantities.json','tests/fixtures/portable-weapons.json','tests/fixtures/portable-damage.json','tests/fixtures/portable-triggers.json','tests/fixtures/portable-combat.json','tests/fixtures/portable-combat-extensions.json','tests/fixtures/portable-autonomous.json','scripts/run-metal-probe.swift']
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    cases=fixtures();programs=[compile_case(c) for c in cases]
    # The same identity may be re-used only with a new bounded generation.
    p,m=compile_case(cases[0]);from portable_specs import LIMITS as L
    p[2]=1;p[L['TARGET_BASE']+2]=0x7fffffff
    p[L['COMMAND_BASE']:L['COMMAND_BASE']+8]=[21,0,0,0,0,0,0,0x408f4000] # t=0, hp=1000
    malformed,malformed_meta=compile_case(cases[0]);malformed[4]=9
    # One shader build/context/dispatch for positives and expected GPU failures.
    # In particular, a second cold CUDA initialization cannot consume the short
    # Windows verification budget after throwing away completed positive output.
    import copy
    full_trace=copy.deepcopy(next(c for c in cases if c['name']=='autonomous-dot-summary'))
    full_trace['combat']['trace']='full';full_trace['script']=[[33,24,0,0,0,-1,0,0]]
    quantity_overflow=copy.deepcopy(next(c for c in cases if c['name']=='ammo-rounds-separate-source-groups'))
    quantity_overflow['effects'][1]['fixed_value']=1e100
    capacity_overflow=copy.deepcopy(quantity_overflow);capacity_overflow['combat']['weapons'][0]['capacity']=1
    capacity_overflow['effects'][1]['fixed_value']=2**31*100
    health_zero=copy.deepcopy(next(c for c in cases if c['name']=='max-hp-only-keeps-current-hp'));health_zero['effects'][0]['fixed_value']=-100
    health_overflow=copy.deepcopy(health_zero);health_overflow['effects'][0]['fixed_value']=1e308
    incoming_overflow=copy.deepcopy(next(c for c in cases if c['name']=='incoming-body-reduction-is-after-defense'));incoming_overflow['effects'][0]['fixed_value']=1e308;incoming_overflow['script'][1][6]=1e30
    definition_overflow,definition_meta=compile_case(cases[0]);definition_overflow[1]=L['DEFINITIONS']+1
    recipient_overflow,recipient_meta=compile_case(cases[0]);recipient_overflow[L['RECIPIENT_BASE']:L['RECIPIENT_BASE']+2]=[7,6]
    recipient_order,recipient_order_meta=compile_case(cases[0]);recipient_order[L['RECIPIENT_BASE']:L['RECIPIENT_BASE']+5]=[8,0,1,0,9]
    resident_overflow=copy.deepcopy(next(c for c in cases if c['name']=='all-512-resident-slots-are-distinct'));resident_overflow['script'] += [[.2,4,0,0,0,-1,0,0],[.2,0,7,4,0,-1,0,0]]
    lazy_capacity=json.loads((ROOT/'tests/fixtures/portable-lazy-capacity-rejection.json').read_text(encoding='utf-8'))
    invalid_lazy,invalid_lazy_meta=compile_case(cases[0]);invalid_lazy[L['RECIPIENT_BASE']+7]=(L['DEFINITIONS']+1)<<4
    poisoned_lazy,poisoned_meta=compile_case(next(c for c in cases if c['name']=='same-caster-time-selector-shares-rank-snapshot'));poisoned_lazy[L['RECIPIENT_BASE']+8+1]=2
    instant_lazy,instant_meta=compile_case(next(c for c in cases if c['name']=='instant-rank-allies_lowest_hp:2'));instant_lazy[L['RECIPIENT_BASE']+7] |= 1<<4
    rejections=[dict(name='target-generation-overflow',status=2),dict(name='wire-target-capacity',status=64),
                dict(name='full-trace-capacity',status=8),dict(name='quantity-int64-range',status=2),dict(name='ammunition-state-range',status=2),dict(name='nonpositive-maximum-hp',status=16),dict(name='health-arithmetic-overflow',status=16),dict(name='incoming-arithmetic-overflow',status=16),dict(name='wire-definition-capacity',status=64),dict(name='wire-recipient-count',status=64),dict(name='wire-recipient-order',status=64),dict(name='resident-carrier-capacity',status=64),dict(name='lazy-cache-capacity',status=64),dict(name='wire-lazy-group',status=64),dict(name='wire-lazy-group-identity',status=64),dict(name='wire-lazy-instant',status=64)]
    negative_programs=[(p,m),(malformed,malformed_meta),compile_case(full_trace),compile_case(quantity_overflow),compile_case(capacity_overflow),compile_case(health_zero),compile_case(health_overflow),compile_case(incoming_overflow),(definition_overflow,definition_meta),(recipient_overflow,recipient_meta),(recipient_order,recipient_order_meta),compile_case(resident_overflow),compile_case(lazy_capacity),(invalid_lazy,invalid_lazy_meta),(poisoned_lazy,poisoned_meta),(instant_lazy,instant_meta)]
    indices=list(range(len(cases),len(cases)+len(rejections)))
    statuses=[0]*len(cases)+[c['status'] for c in rejections]
    try:
        run_programs(programs+negative_programs,backend=args.backend)
    except PortableExecutionError as e:
        result=dict(results=e.results[:len(cases)],**e.evidence,
                    application_event_runtime_connected=True,weapon_burst_target_connected=True,
                    autonomous_battle_connected=False,gpu_timeline_connected=any(m.get('timeline',False) for _,m in programs),actual_statuses=e.statuses)
    except Exception as e:
        path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='execution-failed',error=str(e)))+'\n',encoding='utf-8')
        raise
    else:raise AssertionError('Expected GPU rejection statuses were absent')
    result.update(passed=False,stage='readback-before-comparison',validation_sha256=hashes,
                  batch_layout=dict(positive_count=len(cases),rejection_indices=indices),
                  expected_statuses=statuses)
    # Preserve raw evidence even if a later expectation fails.
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert result['actual_statuses']==statuses,result['actual_statuses']
    negative={**evidence_subset(result), 'case_indices':indices}
    rows=[]
    for c,r in zip(cases,result['results']):
        assert len(r['queries'])==len(c['expected_queries'])
        contains(r['queries'],c['expected_queries'],c['name'])
        if 'expected_targets' in c:contains(r['targets'],c['expected_targets'],c['name']+'.targets')
        if 'equivalent_final_to' in c:
            reference=result['results'][next(i for i,x in enumerate(cases) if x['name']==c['equivalent_final_to'])]
            assert {k:v for k,v in r.items() if k!='queries'}=={k:v for k,v in reference.items() if k!='queries'},c['name']
            assert r['queries'][-1]==reference['queries'][-1],c['name']
        if 'expected_final' in c:contains(r,c['expected_final'],c['name']+'.final')
        if c.get('equivalent_to')=='autonomous-half-second-grid':
            reference=result['results'][next(i for i,x in enumerate(cases) if x['name']==c['equivalent_to'])]
            assert r==reference,c['name']
        if 'expected_burst_trace' in c:
            assert len(r['burst_trace'])==len(c['expected_burst_trace'])
            contains(r['burst_trace'],c['expected_burst_trace'],c['name']+'.burst_trace')
        if 'expected_timers' in c:contains(r['timers'],c['expected_timers'],c['name']+'.timers')
        if 'expected_lazy_cache' in c:contains(r['lazy_cache'],c['expected_lazy_cache'],c['name']+'.lazy_cache')
        if 'minimum_cache_reuses' in c:assert r['lazy_cache']['reuses']>=c['minimum_cache_reuses'],c['name']
        if 'expected_active_carrier_count' in c:
            assert sum(x['active'] for x in r['carriers'])==c['expected_active_carrier_count'],c['name']
        if 'expected_carriers' in c:
            resident=[x for x in r['carriers'] if x['active'] and x['effect'] in c['carrier_effect_names']]
            assert len(resident)==len(c['expected_carriers']),(c['name'],len(resident),len(c['expected_carriers']))
            contains(resident,c['expected_carriers'],c['name']+'.carriers')
        rows.append(dict(name=c['name'],passed=True,actual=r))
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    reference=verify_trigger_reference([c for c in cases if not c.get('health_reference') and not c.get('capacity_reference')])
    damage_reference=verify_damage_reference(cases)
    from portable_capacity_oracle import observe as capacity_observe
    capacity_reference=[]
    for case,gpu in zip(cases,result['results']):
        if case.get('capacity_reference') and 'combat' not in case:
            cpu=capacity_observe(case)
            assert cpu==[q['attack_buffs'] for q in gpu['queries']],case['name']
            capacity_reference.append(case['name'])
    from portable_health_oracle import observe as carrier_observe
    carrier_reference=[]
    for case in cases:
        if not case.get('carrier_reference'):continue
        observed=carrier_observe(case,with_carriers=True)
        resident=[x for x in observed['carriers'] if x['effect'] in case['carrier_effect_names']]
        assert len(resident)==len(case['expected_carriers']),case['name']+'.cpu.carriers'
        contains(resident,case['expected_carriers'],case['name']+'.cpu.carriers')
        carrier_reference.append(case['name'])
    weapon_reference,cpu_differences=verify_weapon_reference(cases)
    health_reference,health_differences=verify_health_reference(cases,result['results'])
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    result.update(lazy_cpu_regressions=[c['name'] for c in cases if c.get('lazy_reference')],carrier_cpu_regressions=carrier_reference,capacity_cpu_regressions=capacity_reference,health_cpu_regressions=health_reference,known_health_cpu_differences=health_differences,known_cpu_differences=cpu_differences,weapon_cpu_regressions=weapon_reference,damage_cpu_regressions=damage_reference,trigger_cpu_regressions=reference,passed=True,stage='verified',cases=rows,validation_sha256=hashes,cpu_trace_used_as_gpu_input=False,
                  rejection_execution=negative,rejected_cases=rejections,
                  scope='Shared bounded weapon modes, physical pellets/muzzles, burst reentry and body/add targets; no general battle acceptance')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,cases=len(rows),device=result['transport']['device'],backend=args.backend)))


if __name__=='__main__':main()
