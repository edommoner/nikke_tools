"""Reuse the authored clock/lifecycle cases on the shared GPU executor.
CPU state and traces are regression outputs only, never GPU inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from portable_runtime import compile_program,run_programs,PortableExecutionError
from timer_registry_cases import cases,prepare,exercise,NAMES
import engine_worker


def compile_case(case):
    bm=prepare(case)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    script=[[0,0,0,0,0,-1,0,0]]
    for i,t in enumerate(case['times']):
        if t in case.get('events',{}):script.append([t,0,7,0,0,-1,0,0])
        script.append([t,2,0,0,-1,i,0,0])
    return compile_program(chars,bm._effects,script,[bm.state['base_stats'][n]['atk'] for n in NAMES])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    parser.add_argument('--short',action='store_true',help='Use the original 14-case CUDA handoff scope')
    args=parser.parse_args()
    report_path=ROOT/f'research/portable-events-{args.backend}{"-short" if args.short else ""}.json'
    report_path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='execution-pending'))+'\n', encoding='utf-8')
    inputs=list(cases());programs=[compile_case(case) for case in inputs]
    extras=json.loads((ROOT/'tests/fixtures/portable-events.json').read_text(encoding='utf-8'))['cases']
    if args.short:extras=extras[:6]
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    for case in extras:
        programs.append(compile_program(chars,[(e,NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))],case['script'],
                                        case['base_atk'],**case.get('environment',{})))
    # Build/dispatch before evaluating the CPU reference: even an accidental
    # dependency on CPU observations cannot become input to this invocation.
    result=run_programs(programs,backend=args.backend)
    rows=[]
    for case,actual in zip(inputs,result['results'][:len(inputs)]):
        totals=[sum(query['damage']) for query in actual['queries']]
        assert totals==case['totals'],(case['name'],totals,case['totals'])
        cpu=exercise(case)
        firings=[(row['effect'],row['time']) for row in actual['trace']]
        assert firings==cpu['firings'],(case['name'],firings,cpu['firings'])
        assert all(q['stack_depth']==0 for q in actual['queries'])
        assert all(row['next_due']>row['time'] for row in actual['trace'])
        rows.append(dict(name=case['name'],passed=True,expected_totals=case['totals'],actual=actual))
    for case,actual in zip(extras,result['results'][len(inputs):]):
        totals=[sum(q['damage']) for q in actual['queries']]
        assert totals==case['expected_totals'],(case['name'],totals,case['expected_totals'])
        if 'expected_attack_buffs' in case:
            assert [q['attack_buffs'][0] for q in actual['queries']]==case['expected_attack_buffs']
        if 'expected_members' in case:
            assert [q['damage'] for q in actual['queries']]==case['expected_members']
        if 'expected_all_attack_buffs' in case:
            assert [q['attack_buffs'] for q in actual['queries']]==case['expected_all_attack_buffs']
        rows.append(dict(name=case['name'],passed=True,expected_totals=case['expected_totals'],actual=actual))
    # Explicit stack and numeric overflow failures must remain GPU errors.
    cycle=[dict(name=name,source='스킬1',type='instant',stat='force_skill_use',target='self',target_skill='스킬1',
                trigger=dict(timing=['battle_start'],condition=[])) for name in ('cycle-a','cycle-b')]
    negative=[compile_program(chars,[(e,NAMES[0]) for e in cycle],[[0,0,0,0,0,-1,0,0]],[1000]*5),
              compile_program(chars,[(extras[1]['effects'][0],NAMES[0])],[[0,0,0,0,0,-1,0,0],[0,18,0,0,-1,-1,1e6,0]],[1e308]*5)]
    try:run_programs(negative,backend=args.backend)
    except PortableExecutionError as error:
        assert error.statuses==[1,16],error.statuses
        negative_evidence=error.evidence
    else:raise AssertionError('Unsafe GPU programs were accepted')
    tracked=['app/portable_runtime.py','app/portable_specs.py','app/portable_backend.py',
             'app/detail_gpu.py','app/effect_spec.py','scripts/timer_registry_cases.py',
             'scripts/verify-portable-events.py','scripts/run-metal-probe.swift','tests/fixtures/portable-events.json']
    result.update(passed=True,cases=rows,cpu_trace_used_as_gpu_input=False,
                  application_event_runtime_connected=True,autonomous_battle_connected=False,
                  rejected_cases=[dict(name='recursive-force-stack-limit',status=1),dict(name='damage-int64-overflow',status=16)],
                  rejection_execution=negative_evidence,
                  adapter_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked})
    report_path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True,cases=len(rows),device=result['transport']['device'],
                         gpu_execution_verified=True,application_event_runtime_connected=True,
                         autonomous_battle_connected=False)))


if __name__=='__main__':main()
