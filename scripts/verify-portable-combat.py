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
    return json.loads((ROOT/'tests/fixtures/portable-combat.json').read_text(encoding='utf-8'))['cases']


def compile_case(case):
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    return compile_program(chars,[(e,NAMES[0]) for e in case['effects']],case['script'],[1000]*5,combat=case['combat'])


def contains(actual,expected,path=''):
    if isinstance(expected,dict):
        for k,v in expected.items():contains(actual[k],v,path+'.'+k)
    elif isinstance(expected,list):
        assert len(actual)>=len(expected),(path,len(actual),len(expected))
        for i,v in enumerate(expected):contains(actual[i],v,path+f'[{i}]')
    else:assert actual==expected,(path,actual,expected)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    args=parser.parse_args();path=ROOT/f'research/portable-combat-{args.backend}.json'
    path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='execution-pending'))+'\n',encoding='utf-8')
    tracked=['app/portable_runtime.py','app/portable_combat.py','app/portable_specs.py','app/portable_backend.py',
             'app/detail_gpu.py','app/effect_spec.py','app/impact_specs.py','app/world_condition_specs.py','scripts/verify-portable-combat.py',
             'tests/fixtures/portable-combat.json','scripts/run-metal-probe.swift']
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    cases=fixtures();programs=[compile_case(c) for c in cases]
    result=run_programs(programs,backend=args.backend)
    rows=[]
    for c,r in zip(cases,result['results']):
        assert len(r['queries'])==len(c['expected_queries'])
        contains(r['queries'],c['expected_queries'],c['name'])
        if 'expected_targets' in c:contains(r['targets'],c['expected_targets'],c['name']+'.targets')
        if 'expected_timers' in c:contains(r['timers'],c['expected_timers'],c['name']+'.timers')
        rows.append(dict(name=c['name'],passed=True,actual=r))
    # The same identity may be re-used only with a new bounded generation.
    p,m=compile_case(cases[0]);from portable_specs import LIMITS as L
    p[2]=1;p[L['TARGET_BASE']+2]=0x7fffffff
    p[L['COMMAND_BASE']:L['COMMAND_BASE']+8]=[21,0,0,0,0,0,0,0x408f4000] # t=0, hp=1000
    malformed,malformed_meta=compile_case(cases[0]);malformed[4]=9
    try:run_programs([(p,m),(malformed,malformed_meta)],backend=args.backend)
    except PortableExecutionError as e:
        assert e.statuses==[2,64],e.statuses;negative=e.evidence
    else:raise AssertionError('Generation overflow accepted')
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    result.update(passed=True,cases=rows,validation_sha256=hashes,cpu_trace_used_as_gpu_input=False,
                  rejection_execution=negative,rejected_cases=[dict(name='target-generation-overflow',status=2),dict(name='wire-target-capacity',status=64)],
                  scope='Bounded fixed-rate/automatic full-charge weapons, simple 1-2-3 burst policy, body/add HP pools and captured periodic generations; no general battle acceptance')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,cases=len(rows),device=result['transport']['device'],backend=args.backend)))


if __name__=='__main__':main()
