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
    return sum((json.loads((ROOT/'tests/fixtures'/name).read_text(encoding='utf-8'))['cases'] for name in ('portable-combat.json','portable-combat-extensions.json','portable-autonomous.json','portable-triggers.json','portable-damage.json','portable-weapons.json','portable-quantities.json','portable-charge-control.json')),[])


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
        contains(queries,case.get('known_cpu_difference',{}).get('expected_queries',case['expected_queries']),case['name']+'.cpu')
        if 'known_cpu_difference' in case:
            differences.append(dict(name=case['name'],reason=case['known_cpu_difference']['reason'],actual_cpu_queries=queries,expected_cpu_queries=case['known_cpu_difference']['expected_queries'],expected_gpu_queries=case['expected_queries']))
        if 'expected_final' in case:
            expected=case['expected_final'].get('weapons',[{}])[0]
            contains(final,{k:v for k,v in expected.items() if k in ('warm','last_interval')},case['name']+'.cpu.final')
        verified.append(case['name'])
    return verified,differences


def evidence_subset(result):
    return {key:result[key] for key in ('transport','source_sha256','generated_sha256',
                                       'input_sha256','output_sha256','gpu_execution_verified','backend')}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    args=parser.parse_args();path=ROOT/f'research/portable-combat-{args.backend}.json'
    path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='execution-pending'))+'\n',encoding='utf-8')
    tracked=['app/portable_runtime.py','app/portable_combat.py','app/portable_specs.py','app/portable_backend.py',
             'app/portable_trigger_specs.py','app/portable_damage_specs.py','scripts/portable_weapon_oracle.py','scripts/verify-detail.py','app/detail_gpu.py','app/effect_spec.py','app/impact_specs.py','app/world_condition_specs.py','scripts/verify-portable-combat.py',
             'tests/fixtures/portable-charge-control.json','tests/fixtures/portable-quantities.json','tests/fixtures/portable-weapons.json','tests/fixtures/portable-damage.json','tests/fixtures/portable-triggers.json','tests/fixtures/portable-combat.json','tests/fixtures/portable-combat-extensions.json','tests/fixtures/portable-autonomous.json','scripts/run-metal-probe.swift']
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
    rejections=[dict(name='target-generation-overflow',status=2),dict(name='wire-target-capacity',status=64),
                dict(name='full-trace-capacity',status=8),dict(name='quantity-int64-range',status=2),dict(name='ammunition-state-range',status=2)]
    negative_programs=[(p,m),(malformed,malformed_meta),compile_case(full_trace),compile_case(quantity_overflow),compile_case(capacity_overflow)]
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
        rows.append(dict(name=c['name'],passed=True,actual=r))
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    reference=verify_trigger_reference(cases)
    damage_reference=verify_damage_reference(cases)
    weapon_reference,cpu_differences=verify_weapon_reference(cases)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    result.update(known_cpu_differences=cpu_differences,weapon_cpu_regressions=weapon_reference,damage_cpu_regressions=damage_reference,trigger_cpu_regressions=reference,passed=True,stage='verified',cases=rows,validation_sha256=hashes,cpu_trace_used_as_gpu_input=False,
                  rejection_execution=negative,rejected_cases=rejections,
                  scope='Shared bounded weapon modes, physical pellets/muzzles, burst reentry and body/add targets; no general battle acceptance')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,cases=len(rows),device=result['transport']['device'],backend=args.backend)))


if __name__=='__main__':main()
