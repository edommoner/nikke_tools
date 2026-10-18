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
    return sum((json.loads((ROOT/'tests/fixtures'/name).read_text(encoding='utf-8'))['cases'] for name in ('portable-combat.json','portable-combat-extensions.json')),[])


def compile_case(case):
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    return compile_program(chars,[(e,NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))],case['script'],[1000]*5,combat=case['combat'])


def contains(actual,expected,path=''):
    if isinstance(expected,dict):
        for k,v in expected.items():contains(actual[k],v,path+'.'+k)
    elif isinstance(expected,list):
        assert len(actual)>=len(expected),(path,len(actual),len(expected))
        for i,v in enumerate(expected):contains(actual[i],v,path+f'[{i}]')
    else:assert actual==expected,(path,actual,expected)


def evidence_subset(result):
    return {key:result[key] for key in ('transport','source_sha256','generated_sha256',
                                       'input_sha256','output_sha256','gpu_execution_verified','backend')}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    args=parser.parse_args();path=ROOT/f'research/portable-combat-{args.backend}.json'
    path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='execution-pending'))+'\n',encoding='utf-8')
    tracked=['app/portable_runtime.py','app/portable_combat.py','app/portable_specs.py','app/portable_backend.py',
             'app/detail_gpu.py','app/effect_spec.py','app/impact_specs.py','app/world_condition_specs.py','scripts/verify-portable-combat.py',
             'tests/fixtures/portable-combat.json','tests/fixtures/portable-combat-extensions.json','scripts/run-metal-probe.swift']
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
    statuses=[0]*len(cases)+[2,64]
    try:
        run_programs(programs+[(p,m),(malformed,malformed_meta)],backend=args.backend)
    except PortableExecutionError as e:
        result=dict(results=e.results[:len(cases)],**e.evidence,
                    application_event_runtime_connected=True,weapon_burst_target_connected=True,
                    autonomous_battle_connected=False,actual_statuses=e.statuses)
    except Exception as e:
        path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='execution-failed',error=str(e)))+'\n',encoding='utf-8')
        raise
    else:raise AssertionError('Expected GPU rejection statuses were absent')
    result.update(passed=False,stage='readback-before-comparison',validation_sha256=hashes,
                  batch_layout=dict(positive_count=len(cases),rejection_indices=[len(cases),len(cases)+1]),
                  expected_statuses=statuses)
    # Preserve raw evidence even if a later expectation fails.
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert result['actual_statuses']==statuses,result['actual_statuses']
    negative={**evidence_subset(result), 'case_indices':[len(cases),len(cases)+1]}
    rows=[]
    for c,r in zip(cases,result['results']):
        assert len(r['queries'])==len(c['expected_queries'])
        contains(r['queries'],c['expected_queries'],c['name'])
        if 'expected_targets' in c:contains(r['targets'],c['expected_targets'],c['name']+'.targets')
        if 'expected_burst_trace' in c:
            assert len(r['burst_trace'])==len(c['expected_burst_trace'])
            contains(r['burst_trace'],c['expected_burst_trace'],c['name']+'.burst_trace')
        if 'expected_timers' in c:contains(r['timers'],c['expected_timers'],c['name']+'.timers')
        rows.append(dict(name=c['name'],passed=True,actual=r))
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    result.update(passed=True,stage='verified',cases=rows,validation_sha256=hashes,cpu_trace_used_as_gpu_input=False,
                  rejection_execution=negative,rejected_cases=[dict(name='target-generation-overflow',status=2),dict(name='wire-target-capacity',status=64)],
                  scope='Shared bounded weapon modes, physical pellets/muzzles, burst reentry and body/add targets; no general battle acceptance')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,cases=len(rows),device=result['transport']['device'],backend=args.backend)))


if __name__=='__main__':main()
