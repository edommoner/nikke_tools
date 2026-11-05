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
    return sum((json.loads((ROOT/'tests/fixtures'/name).read_text(encoding='utf-8'))['cases'] for name in ('portable-combat.json','portable-combat-extensions.json','portable-autonomous.json','portable-triggers.json','portable-damage.json','portable-weapons.json','portable-quantities.json','portable-charge-control.json','portable-health.json','portable-hp-edges.json','portable-incoming.json','portable-capacity.json','portable-recipients.json','portable-carriers.json','portable-lazy.json','portable-bullets.json','portable-burst-resources.json','portable-enemy-damage.json','portable-cover.json','portable-pending-burst.json','portable-burst-duration.json','portable-ammo-instants.json','portable-ammo-modes.json','portable-mode-sessions.json','portable-buff-notices.json','portable-enemy-buffs.json','portable-event-candidates.json','portable-enemy-attack-ranks.json','portable-enemy-spawn-order.json','portable-enemy-auto-aim.json','portable-periodic-targets.json','portable-resources.json','portable-hit-references.json','portable-reference-scales.json','portable-sources.json','portable-staged.json','portable-lifesteal-prototype.json','portable-landings.json','portable-removal.json','portable-duration-extend.json','portable-stacks.json','portable-status.json','portable-protection.json','portable-split.json','portable-instant-lists.json','portable-named-states.json','portable-enemy-codes.json','portable-element-overrides.json','portable-probability.json','portable-geometry.json','portable-target-states.json','portable-attack-flags.json','portable-burst-charge-speed.json','portable-burst-charge-skills.json','portable-hp-attack.json','portable-mode-entry.json','portable-pending-reference.json','portable-enemy-targets.json','portable-mode-enemy-names.json')),[])


def compile_case(case):
    if not case.get('mode_entry_reference') and not case.get('pending_scale_reference'):return _compile_case(case)
    from contextlib import ExitStack
    with ExitStack() as stack:
        if case.get('mode_entry_reference'):
            from portable_mode_entry_oracle import data_context
            stack.enter_context(data_context(case))
        if case.get('pending_scale_reference'):
            from portable_pending_reference_context import data_context
            stack.enter_context(data_context(case))
        return _compile_case(case)


def _compile_case(case):
    # A mode without reload_time inherits its authored base weapon, just as
    # the independent native observer does; never borrow catalog timing from
    # the arbitrary names used to identify these mechanical test actors.
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=dict(engine_worker.META[n])) for n in NAMES]
    if 'combat' in case:
        for char,weapon in zip(chars,case['combat']['weapons']):
            char['_weapon']['reload_time']=weapon.get('reload',1)
    environment=dict(case.get('environment',{}))
    if 'enemy_targeting' in case:environment['enemy_targeting']=case['enemy_targeting']
    return compile_program(chars,[(e,NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))],case['script'],case.get('base_atk',[1000]*5),combat=case.get('combat'),**environment)


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
        if case.get('code_reference') or case.get('named_state_reference') or case.get('protection_reference') or case.get('split_reference') or case.get('instant_list_reference') or case.get('resource_reference') or case.get('source_reference') or case.get('scale_reference') or 'combat' in case or 'damage_reference' in case and not case.get('trigger_reference'):continue
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
