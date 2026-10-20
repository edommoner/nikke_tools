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
    return sum((json.loads((ROOT/'tests/fixtures'/name).read_text(encoding='utf-8'))['cases'] for name in ('portable-combat.json','portable-combat-extensions.json','portable-autonomous.json','portable-triggers.json','portable-damage.json','portable-weapons.json','portable-quantities.json','portable-charge-control.json','portable-health.json','portable-hp-edges.json','portable-incoming.json','portable-capacity.json','portable-recipients.json','portable-carriers.json','portable-lazy.json','portable-bullets.json','portable-burst-resources.json','portable-enemy-damage.json','portable-cover.json','portable-pending-burst.json','portable-burst-duration.json','portable-ammo-instants.json','portable-ammo-modes.json','portable-mode-sessions.json','portable-buff-notices.json','portable-enemy-buffs.json','portable-event-candidates.json','portable-enemy-attack-ranks.json','portable-enemy-spawn-order.json','portable-enemy-auto-aim.json','portable-periodic-targets.json','portable-resources.json','portable-hit-references.json','portable-reference-scales.json','portable-sources.json','portable-staged.json','portable-lifesteal-prototype.json','portable-landings.json','portable-removal.json','portable-duration-extend.json','portable-stacks.json','portable-status.json','portable-protection.json','portable-split.json','portable-instant-lists.json','portable-named-states.json')),[])


def compile_case(case):
    # A mode without reload_time inherits its authored base weapon, just as
    # the independent native observer does; never borrow catalog timing from
    # the arbitrary names used to identify these mechanical test actors.
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=dict(engine_worker.META[n])) for n in NAMES]
    if 'combat' in case:
        for char,weapon in zip(chars,case['combat']['weapons']):
            char['_weapon']['reload_time']=weapon.get('reload',1)
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
        if case.get('named_state_reference') or case.get('protection_reference') or case.get('split_reference') or case.get('instant_list_reference') or case.get('resource_reference') or case.get('source_reference') or case.get('scale_reference') or 'combat' in case or 'damage_reference' in case and not case.get('trigger_reference'):continue
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
    tracked=['app/portable_duration_extend_specs.py','scripts/portable_duration_extend_oracle.py','tests/fixtures/portable-duration-extend.json','app/portable_removal_specs.py','scripts/portable_removal_oracle.py','tests/fixtures/portable-removal.json','app/portable_lifesteal_reference.py','scripts/portable_lifesteal_oracle.py','scripts/portable_landing_oracle.py','tests/fixtures/portable-lifesteal-prototype.json','tests/fixtures/portable-landings.json','app/portable_staged_specs.py','app/staged_dot_specs.py','app/staged_dot_runtime.py','tests/fixtures/portable-staged.json','app/portable_source_specs.py','scripts/portable_source_oracle.py','app/periodic_source_specs.py','app/periodic_source_runtime.py','tests/fixtures/portable-sources.json','app/reference_count_runtime.py','app/reference_health_runtime.py','app/engine_compat.py','tests/fixtures/portable-reference-scales.json','app/portable_reference_specs.py','tests/fixtures/portable-hit-references.json','app/portable_resource_specs.py','app/portable_resource_decode.py','app/resource_specs.py','app/resource_runtime.py','scripts/portable_resource_oracle.py','tests/fixtures/portable-resources.json','app/portable_roster_input.py','app/portable_runtime_layout.py','app/portable_enemy_specs.py','app/portable_runtime.py','app/portable_combat.py','app/portable_specs.py','app/portable_periodic_specs.py','app/portable_backend.py',
             'app/portable_trigger_specs.py','app/portable_recipient_specs.py','app/portable_damage_specs.py','scripts/portable_pending_oracle.py','app/named_target_specs.py','scripts/portable_capacity_oracle.py','scripts/portable_health_oracle.py','scripts/portable_enemy_oracle.py','scripts/portable_burst_oracle.py','scripts/portable_bullet_oracle.py','scripts/portable_weapon_oracle.py','scripts/verify-detail.py','app/detail_gpu.py','app/effect_spec.py','app/impact_specs.py','app/world_condition_specs.py','scripts/verify-portable-combat.py',
             'tests/fixtures/portable-event-candidates.json','tests/fixtures/portable-enemy-attack-ranks.json','tests/fixtures/portable-enemy-spawn-order.json','tests/fixtures/portable-enemy-auto-aim.json','tests/fixtures/portable-periodic-targets.json','scripts/portable_enemy_buff_oracle.py','tests/fixtures/portable-enemy-buffs.json','research/portable-mode-session-contract.json','tests/fixtures/portable-buff-notices.json','tests/fixtures/portable-mode-sessions.json','tests/fixtures/portable-ammo-modes.json','tests/fixtures/portable-ammo-instants.json','tests/fixtures/portable-burst-duration.json','tests/fixtures/portable-pending-burst.json','tests/fixtures/portable-cover.json','tests/fixtures/portable-enemy-damage.json','tests/fixtures/portable-burst-resources.json','tests/fixtures/portable-bullets.json','tests/fixtures/portable-lazy.json','tests/fixtures/portable-lazy-capacity-rejection.json','tests/fixtures/portable-carriers.json','tests/fixtures/portable-recipients.json','tests/fixtures/portable-capacity.json','tests/fixtures/portable-incoming.json','tests/fixtures/portable-hp-edges.json','tests/fixtures/portable-health.json','tests/fixtures/portable-charge-control.json','tests/fixtures/portable-quantities.json','tests/fixtures/portable-weapons.json','tests/fixtures/portable-damage.json','tests/fixtures/portable-triggers.json','tests/fixtures/portable-combat.json','tests/fixtures/portable-combat-extensions.json','tests/fixtures/portable-autonomous.json','scripts/run-metal-probe.swift']
    tracked += ['tests/fixtures/portable-lazy-capacity-rejection.json','tests/fixtures/portable-lazy-cleanse-capacity-rejection.json','app/portable_status_specs.py','scripts/portable_status_oracle.py','scripts/portable_status_validation.py','tests/fixtures/portable-status.json','scripts/portable_bullet_oracle.py']
    tracked += ['scripts/portable_carrier_observer.py','app/weapon_mode_runtime.py','app/portable_stack_specs.py','scripts/portable_stack_oracle.py','scripts/portable_stack_validation.py','tests/fixtures/portable-stacks.json']
    tracked += ['app/portable_protection_specs.py','app/protection_runtime.py','scripts/portable_protection_oracle.py','scripts/portable_protection_validation.py','tests/fixtures/portable-protection.json','tests/fixtures/portable-split.json','scripts/portable_split_validation.py','scripts/portable_instant_list_oracle.py','scripts/portable_instant_list_validation.py','tests/fixtures/portable-instant-lists.json']
    tracked += ['scripts/portable_named_state_oracle.py','scripts/portable_named_state_validation.py','tests/fixtures/portable-named-states.json']
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
    lazy_capacity=json.loads((ROOT/'tests/fixtures/portable-lazy-cleanse-capacity-rejection.json').read_text(encoding='utf-8'))
    invalid_lazy,invalid_lazy_meta=compile_case(cases[0]);invalid_lazy[L['RECIPIENT_BASE']+7]=(L['DEFINITIONS']+1)<<4
    poisoned_lazy,poisoned_meta=compile_case(next(c for c in cases if c['name']=='same-caster-time-selector-shares-rank-snapshot'));poisoned_lazy[L['RECIPIENT_BASE']+8+1]=2
    instant_lazy,instant_meta=compile_case(next(c for c in cases if c['name']=='instant-rank-allies_lowest_hp:2'));instant_lazy[L['RECIPIENT_BASE']+7] |= 1<<4
    bullet_count,bullet_count_meta=compile_case(cases[0]);bullet_count[L['BULLET_DEFINITION_BASE']]=2**31
    bullet_kind,bullet_kind_meta=compile_case(next(c for c in cases if c['name']=='instant-rank-allies_lowest_hp:2'));bullet_kind[L['BULLET_DEFINITION_BASE']]=1
    bullet_bound,bullet_bound_meta=compile_case(cases[0]);bullet_bound[L['BULLET_DEFINITION_BASE']:L['BULLET_DEFINITION_BASE']+2]=[1,2]
    burst_without_combat,burst_without_meta=compile_case(next(c for c in cases if c['name']=='cast-instant-reduces-new-ready-time'));burst_without_combat[3]=0;burst_without_combat[L['TARGET_ATTACK_BASE']:L['TARGET_ATTACK_BASE']+16]=[0]*16
    burst_recipient,burst_recipient_meta=compile_case(next(c for c in cases if c['name']=='gauge-allied-instant-25'));burst_recipient[L['RECIPIENT_BASE']]=14
    burst_overflow=copy.deepcopy(next(c for c in cases if c['name']=='negative-instant-extends-new-cooldown'))
    burst_overflow['effects'][0]['fixed_value']=-1e308;burst_overflow['effects'][0]['trigger']['timing']=['on_attack']
    burst_overflow['script']=[[0,0,7,0,0,-1,0,0],[0,0,7,0,0,-1,0,0]]
    enemy_bad=[];enemy_rejections=[]
    for name,offset,value in [('route',0,10),('count-zero',1,0),('count-range',1,257),('hits-range',2,257),('normal-kind',3,2)]:
        words,meta=compile_case(next(c for c in cases if c['name']=='all-enemies-single-packet'))
        words[L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-'+name,status=64))
    for name,payload in [('gauge-nan',[0,0x7ff80000]),('gauge-negative',[0,0xbfe00000])]:
        words,meta=compile_case(next(c for c in cases if c['name']=='all-enemies-single-packet'))
        at=L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+4;words[at:at+2]=payload
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-'+name,status=64))
    words,meta=compile_case(next(c for c in cases if c['name']=='all-enemies-single-packet'))
    from portable_specs import FIELDS as F
    from portable_runtime import double_words
    at=L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['INTERVAL'];words[at:at+2]=double_words(.25)
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-periodic-missing-retained-policy',status=64))
    words,meta=compile_case(next(c for c in cases if c['name']=='enemy-selector-enemies_top_def-1'))
    at=L['TARGET_BASE']+L['TARGET_WORDS']+6;words[at:at+2]=double_words(1)
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-defense-policy',status=64))
    words,meta=compile_case(next(c for c in cases if c['name']=='all-enemies-single-packet'));words[3]=0
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-without-combat',status=64))
    many=copy.deepcopy(next(c for c in cases if c['name']=='256-hits-summary-retains-all-notifications'));many['combat']['trace']='full'
    enemy_bad.append(compile_case(many));enemy_rejections.append(dict(name='enemy-logical-hit-trace-capacity',status=8))
    rejections=[dict(name='target-generation-overflow',status=2),dict(name='wire-target-capacity',status=64),
                dict(name='full-trace-capacity',status=8),dict(name='quantity-int64-range',status=2),dict(name='ammunition-state-range',status=2),dict(name='nonpositive-maximum-hp',status=16),dict(name='health-arithmetic-overflow',status=16),dict(name='incoming-arithmetic-overflow',status=16),dict(name='wire-definition-capacity',status=64),dict(name='wire-recipient-count',status=64),dict(name='wire-recipient-order',status=64),dict(name='resident-carrier-capacity',status=64),dict(name='lazy-cache-after-cleanse-capacity',status=64),dict(name='wire-lazy-group',status=64),dict(name='wire-lazy-group-identity',status=64),dict(name='wire-lazy-instant',status=64),dict(name='wire-bullet-count',status=64),dict(name='wire-bullet-kind',status=64),dict(name='wire-bullet-bound',status=64),dict(name='wire-burst-without-combat',status=64),dict(name='wire-burst-recipient',status=64),dict(name='burst-cooldown-arithmetic-overflow',status=16)]
    negative_programs=[(p,m),(malformed,malformed_meta),compile_case(full_trace),compile_case(quantity_overflow),compile_case(capacity_overflow),compile_case(health_zero),compile_case(health_overflow),compile_case(incoming_overflow),(definition_overflow,definition_meta),(recipient_overflow,recipient_meta),(recipient_order,recipient_order_meta),compile_case(resident_overflow),compile_case(lazy_capacity),(invalid_lazy,invalid_lazy_meta),(poisoned_lazy,poisoned_meta),(instant_lazy,instant_meta),(bullet_count,bullet_count_meta),(bullet_kind,bullet_kind_meta),(bullet_bound,bullet_bound_meta),(burst_without_combat,burst_without_meta),(burst_recipient,burst_recipient_meta),compile_case(burst_overflow)]
    words,meta=compile_case(cases[0]);words[6]=2
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-combat-clock-mode',status=64))
    words,meta=compile_case(cases[0]);words[6]=1
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-accumulated-clock-explicit-frame',status=64))
    for name,offset,value in [('cover-policy',7,2),('cover-zero-base',L['COVER_BASE']+1,0),('cover-negative-current',L['COVER_BASE']+3,0xbff00000),('cover-nan-current',L['COVER_BASE']+3,0x7ff80000),('cover-scaling',L['HEALTH_DEFINITION_BASE'],2)]:
        words,meta=compile_case(cases[0]);words[offset]=value;enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-'+name,status=64))
    from portable_runtime import double_words
    from portable_specs import FIELDS as F
    pending_fixture=next(c for c in cases if c['name']=='pending-later-burst-buff-excluded')
    words,meta=compile_case(pending_fixture);words[L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+6]=2
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-pending-flag',status=64))
    words,meta=compile_case(pending_fixture);words[L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+7]=0
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-pending-zero-hits',status=64))
    words,meta=compile_case(pending_fixture);words[L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+7]=257
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-pending-hit-capacity',status=64))
    words,meta=compile_case(pending_fixture);words[3]=0
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-pending-without-controller',status=64))
    for name,bit in [('foreign-owner',0),('non-buff',1),('beyond-definitions',31)]:
        words,meta=compile_case(pending_fixture);words[L['PENDING_EXCLUDE_BASE']+L['MASK_WORDS']]=1<<bit
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-pending-exclusion-'+name,status=64))
    words,meta=compile_case(cases[0]);words[L['PENDING_EXCLUDE_BASE']]=1
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-pending-exclusion-on-ordinary-definition',status=64))
    overflow=copy.deepcopy(next(c for c in cases if c['name']=='pending-all-512-queue-slots'));overflow['script'].insert(-1,[.2,0,19,2,0,-1,0,0])
    enemy_bad.append(compile_case(overflow));enemy_rejections.append(dict(name='pending-queue-capacity',status=64))
    full_pending=copy.deepcopy(next(c for c in cases if c['name']=='pending-512-captures-flush-with-identical-amounts'));full_pending['combat']['trace']='full'
    enemy_bad.append(compile_case(full_pending));enemy_rejections.append(dict(name='pending-full-trace-capacity',status=8))
    duration_fixture=next(c for c in cases if c['name']=='duration-plus-two')
    for name,offset,value in [('zero-group',L['DURATION_DEFINITION_BASE']+2,0),('group-capacity',L['DURATION_DEFINITION_BASE']+2,L['DEFINITIONS']+1),('cast-flag',L['DURATION_DEFINITION_BASE']+3,2),('cast-mismatch',L['DURATION_DEFINITION_BASE']+3,0)]:
        words,meta=compile_case(duration_fixture);words[offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-duration-'+name,status=64))
    words,meta=compile_case(duration_fixture);words[3]=0
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-duration-without-controller',status=64))
    words,meta=compile_case(cases[0]);words[L['DURATION_DEFINITION_BASE']]=1
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-duration-on-other-stat',status=64))
    words,meta=compile_case(cases[0]);words[5]=3
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-trace-policy',status=64))
    duration_overflow=copy.deepcopy(duration_fixture);duration_overflow['effects'] += [dict(e,name='overflow-'+str(i),fixed_value=1e308) for i,e in enumerate([duration_fixture['effects'][1]]*2)];duration_overflow['owners'] += [2,2]
    enemy_bad.append(compile_case(duration_overflow));enemy_rejections.append(dict(name='duration-arithmetic-overflow',status=16))
    group_fixture=next(c for c in cases if c['name']=='duration-independent-noncast-effects-add')
    words,meta=compile_case(group_fixture);words[L['DURATION_DEFINITION_BASE']+4]=1
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-duration-group-owner-conflict',status=64))
    for name,field,value in [('trigger-capacity',F['TRIGGER_COUNT'],L['TRIGGERS']+1),('condition-capacity',F['CONDITION_COUNT'],L['CONDITIONS']+1)]:
        words,meta=compile_case(duration_fixture);words[L['DEFINITION_BASE']+L['DEFINITION_WORDS']+field]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-duration-'+name,status=64))
    ammo_fixture=next(c for c in cases if c['name']=='ammo-pct-5-10')
    for name,offset,value in [('cancel-policy',L['WEAPON_QUANTITY_BASE']+3,2),('named-flag',L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['TARGET'],2)]:
        words,meta=compile_case(ammo_fixture);words[offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-ammo-'+name,status=64))
    words,meta=compile_case(ammo_fixture);words[3]=0
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-ammo-without-controller',status=64))
    words,meta=compile_case(ammo_fixture);at=L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['VALUE'];words[at:at+2]=[0,0x7ff80000]
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-ammo-nan',status=64))
    for name,value,cap in [('flat-negative-overflow',-1e100,5),('flat-state-underflow',-2147483649.,1),('percentage-product-overflow',1e308,10000)]:
        c=copy.deepcopy(ammo_fixture);c['effects'][1]['stat']='ammo_charge_pct' if name.startswith('percentage') else 'ammo_charge_flat';c['effects'][1]['fixed_value']=value;c['combat']['weapons'][0]['capacity']=cap
        enemy_bad.append(compile_case(c));enemy_rejections.append(dict(name='ammo-'+name,status=16))
    mode_fixture=next(c for c in cases if c['name']=='mode-entry-is-squad-broadcast')
    words,meta=compile_case(mode_fixture);words[L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['TARGET']]=2
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-mode-entry-name-flag',status=64))
    recursive_mode=copy.deepcopy(next(c for c in cases if c['name']=='mode-entry-force-refresh-is-synchronous-and-budgeted'))
    recursive_mode['effects'][2]['max_trigger']=-1
    enemy_bad.append(compile_case(recursive_mode));enemy_rejections.append(dict(name='mode-entry-recursive-depth-limit',status=1))
    notice_fixture=next(c for c in cases if c.get('named_buff_reference'))
    for name,offset,value in [('flags',2,4),('reserved',3,1)]:
        words,meta=compile_case(notice_fixture);words[L['HEALTH_DEFINITION_BASE']+offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-buff-notice-'+name,status=64))
    recursive_notice=copy.deepcopy(next(c for c in cases if c['name']=='buff-bounded-self-refresh-preserves-initial-stack-notice'))
    recursive_notice['effects'][0]['max_trigger']=-1
    enemy_bad.append(compile_case(recursive_notice));enemy_rejections.append(dict(name='buff-notice-recursive-depth-limit',status=1))
    enemy_buff_fixture=next(c for c in cases if c.get('enemy_buff_reference'))
    for name,offset,value in [('flag',L['HEALTH_DEFINITION_BASE']+3,2),('no-combat',3,0),('unsupported-stat',L['DEFINITION_BASE']+F['STAT'],0),('zero-count',L['DAMAGE_DEFINITION_BASE']+1,0),('count-overflow',L['DAMAGE_DEFINITION_BASE']+1,257),('ally-selector',L['RECIPIENT_BASE'],0),('missing-flag',L['HEALTH_DEFINITION_BASE']+3,0)]:
        words,meta=compile_case(enemy_buff_fixture);words[offset]=value
        if name=='no-combat':words[L['TARGET_ATTACK_BASE']:L['TARGET_ATTACK_BASE']+16]=[0]*16
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-buff-'+name,status=64))
    for name,target in [('query-negative',0xfffffffe),('query-outside-world',8)]:
        words,meta=compile_case(enemy_buff_fixture);query=next(i for i,x in enumerate(enemy_buff_fixture['script']) if x[1]==2)
        words[L['COMMAND_BASE']+query*8+5]=target
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-buff-'+name,status=64))
    for name,stat in [('flat-overflow','def_caster_based_pct'),('sum-overflow','received_dmg_pct')]:
        overflow=copy.deepcopy(enemy_buff_fixture)
        overflow['effects']=[dict(overflow['effects'][0],name='overflow'+str(i),stat=stat,fixed_value=1e308) for i in range(2)]
        overflow['owners']=[0,0]
        enemy_bad.append(compile_case(overflow));enemy_rejections.append(dict(name='enemy-buff-'+name,status=16))
    candidate_fixture=next(c for c in cases if c['name']=='received-count-1')
    for name,offset,value in [('missing',32*L['MASK_WORDS'],0),('spurious-event',7*L['MASK_WORDS'],1),('padding',32*L['MASK_WORDS']+L['MASK_WORDS']-1,0x80000000)]:
        words,meta=compile_case(candidate_fixture);words[L['EVENT_CANDIDATE_BASE']+offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-event-candidate-'+name,status=64))
    attack_fixture=next(c for c in cases if c['name']=='enemy-attack-add-above-body')
    for name,payload,target in [('nan',[0,0x7ff80000],0),('infinity',[0,0x7ff00000],1),('negative',double_words(-1),2),('range',double_words(1e31),0),('padding',double_words(1),7)]:
        words,meta=compile_case(attack_fixture);at=L['TARGET_ATTACK_BASE']+target*2;words[at:at+2]=payload
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-attack-'+name,status=64))
    words,meta=compile_case(next(c for c in cases if 'combat' not in c));words[L['TARGET_ATTACK_BASE']]=1
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-attack-no-combat',status=64))
    for name in ('defense-high','defense-low'):
        words,meta=compile_case(next(c for c in cases if c['name']=='enemy-spawn-buff-'+name))
        at=L['TARGET_BASE']+L['TARGET_WORDS']+6;words[at:at+2]=double_words(1)
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-enemy-buff-add-'+name,status=64))
    aim_fixture=next(c for c in cases if c['name']=='enemy-auto-aim-initial-policy')
    words,meta=compile_case(aim_fixture);words[L['AIM_POLICY_BASE']]=32
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-auto-aim-owner-mask',status=64))
    words,meta=compile_case(next(c for c in cases if 'combat' not in c));words[L['AIM_POLICY_BASE']]=1
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-auto-aim-without-combat',status=64))
    for name,owner,arg in [('policy',0,2),('owner',5,1),('negative-policy',0,0xffffffff)]:
        words,meta=compile_case(aim_fixture);at=L['COMMAND_BASE'];words[at:at+8]=[27,0,0,0,owner,arg,0xffffffff,0]
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-auto-aim-command-'+name,status=64))
    periodic_fixture=next(c for c in cases if c['name']=='periodic-target-named-alias-unions-in-insertion-order')
    for name,offset,value in [('unknown-flags',L['PERIODIC_DEFINITION_BASE']+2,8),('group-range',L['PERIODIC_DEFINITION_BASE']+3,L['DEFINITIONS']+1),('missing-group',L['PERIODIC_DEFINITION_BASE']+5,0),('group-singleton',L['PERIODIC_DEFINITION_BASE']+5,3),('missing-name-policy',L['PERIODIC_DEFINITION_BASE']+2,1),('name-mismatch',L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F['NAME'],0),('group-stack-policy',L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F['MAX_STACK'],2),('group-clock-family',L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F['PRESERVE'],0)]:
        words,meta=compile_case(periodic_fixture);words[offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-periodic-'+name,status=64))
    for name,fixture,flags in [('retained-without-selection','target-generation-stale-dot-cancelled',5),('own-stack-non-dot','periodic-target-auto_damage-delayed',7),('named-buff-without-damage-clock','periodic-target-dot_damage-delayed',4)]:
        template=next((c for c in cases if c['name']==fixture),None)
        if template is None:template=periodic_fixture
        words,meta=compile_case(template)
        at=L['PERIODIC_DEFINITION_BASE']+(2 if name!='named-buff-without-damage-clock' else 0)
        words[at]=flags
        if name=='retained-without-selection':words[L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']]=0
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-periodic-'+name,status=64))
    resource_fixture=next(c for c in cases if c.get('resource_reference'))
    resource_at=L['RESOURCE_DEFINITION_BASE']
    for name,offset,value in [('count',L['RESOURCE_META_BASE'],257),('reserved',L['RESOURCE_META_BASE']+1,1),('operation',resource_at,6),('missing-key',resource_at+1,0),('unknown-key',resource_at+1,257),('flags',resource_at+2,4),('cap-nan',resource_at+5,0x7ff80000),('cap-negative',resource_at+5,0xbff00000),('minimum-negative',resource_at+19,0xbff00000),('literal-on-charge',resource_at+7,0x3ff00000)]:
        words,meta=compile_case(resource_fixture);words[offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-resource-'+name,status=64))
    for name,fixture,offset in [('zero-step','resource-duplicate-descriptors-unique-boundary-events',L['EVENT_BASE']+L['EVENT_WORDS']+2),('zero-modulus','resource-modulo-beyond-int64-and-negative-truncation',L['CONDITION_BASE']+L['CONDITION_WORDS']+3)]:
        words,meta=compile_case(next(c for c in cases if c['name']==fixture));words[offset]=0
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-resource-'+name,status=64))
    reference_fixture=next(c for c in cases if c['name']=='reference-suffix-fraction')
    reference=L['REFERENCE_DEFINITION_BASE']+2*4
    for name,offset,value in [('mode',reference,3),('reserved',reference+3,1),('missing-key',reference+1,0),('unknown-key',reference+1,257),('name',reference+2,256),('wrong-kind',L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F['KIND'],4),('resource-name',L['RESOURCE_NAME_BASE'],256),('orphan-name',L['REFERENCE_DEFINITION_BASE']+2,7)]:
        words,meta=compile_case(reference_fixture);words[offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-hit-reference-'+name,status=64))
    for name,quantity,status in [('count-257',257,2),('count-beyond-int64',1e30,2),('full-trace-overflow',129,8)]:
        case=copy.deepcopy(reference_fixture);case['effects'][1]['fixed_value']=quantity
        enemy_bad.append(compile_case(case));enemy_rejections.append(dict(name='hit-reference-'+name,status=status))
    scale_fixture=next(c for c in cases if c['name']=='scale-registered-zero-is-held')
    scale_at=L['REFERENCE_DEFINITION_BASE']+4
    for name,offset,value in [('missing-key',scale_at+1,0),('unknown-key',scale_at+1,257<<9),('name-overflow',scale_at+2,1<<16),('reserved-word',scale_at+3,1),('unknown-bits',scale_at,16),('buff-as-dot',scale_at,12),('missing-marker',L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['FLAGS'],0)]:
        words,meta=compile_case(scale_fixture);words[offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-scale-reference-'+name,status=64))
    source_fixture=next(c for c in cases if c['name']=='source-population-expiry-and-phase')
    source_at=L['SOURCE_DEFINITION_BASE']
    from portable_runtime import double_words
    for name,field,payload in [('name',0,[256]),('zero-slots',1,[0]),('too-many-slots',1,[33]),('legacy',2,[2]),('reserved',3,[1]),('zero-base',4,double_words(0)),('nan-base',4,[0,0x7ff80000]),('reduction',6,double_words(101)),('nonpositive-factor',6,double_words(50)),('negative-life',8,double_words(-2)),('large-life',8,double_words(86401)),('nonzero-padding',14,double_words(1)),('metadata-on-buff',L['SOURCE_DEFINITION_WORDS']+3,[1])]:
        words,meta=compile_case(source_fixture);words[source_at+field:source_at+field+len(payload)]=payload
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-source-'+name,status=64))
    for name,field in [('scalar',F['VALUE']),('duration',F['DURATION']),('interval',F['INTERVAL'])]:
        words,meta=compile_case(source_fixture);at=L['DEFINITION_BASE']+field;words[at:at+2]=double_words(1)
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-source-forbidden-'+name,status=64))
    words,meta=compile_case(next(c for c in cases if c['name']=='source-capacity-256-variants'))
    for row in range(65):words[source_at+row*L['SOURCE_DEFINITION_WORDS']]=row
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-source-65-unique-owner-names',status=64))
    staged_fixture=next(c for c in cases if c['name']=='staged-triangular-and-post-period')
    staged_at=L['STAGED_DEFINITION_BASE']+2*8
    for name,field,payload in [('flag',0,[2]),('count',1,[65]),('unknown-resource',1,[512]),('zero-gap',2,double_words(0)),('nan-gap',2,[0,0x7ff80000]),('large-gap',2,double_words(61)),('negative-post',4,double_words(-1)),('large-post',4,double_words(3601)),('override',6,[66]),('parent-zero',7,[0]),('self-parent',7,[3]),('parent-overflow',7,[257])]:
        words,meta=compile_case(staged_fixture);words[staged_at+field:staged_at+field+len(payload)]=payload
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-staged-'+name,status=64))
    words,meta=compile_case(staged_fixture);words[L['STAGED_DEFINITION_BASE']+1]=1
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-staged-disabled-padding',status=64))
    for name,field,value in [('count',0,257),('missing',0,0),('wrong-row',1,1),('out-of-range',1,256),('padding',2,1)]:
        words,meta=compile_case(staged_fixture);words[L['STAGED_INDEX_BASE']+field]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-staged-index-'+name,status=64))
    landing_fixture=next(c for c in cases if c['name']=='landing-native-next-frame')
    for name,field,value in [('policy',0,2),('reserved',1,1),('last-reserved',7,1)]:
        words,meta=compile_case(landing_fixture);words[L['LANDING_META_BASE']+field]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-landing-'+name,status=64))
    words,meta=compile_case(next(c for c in cases if 'combat' not in c));words[L['LANDING_META_BASE']]=1
    enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-landing-without-combat',status=64))
    for name,field,value in [('disabled',L['LANDING_META_BASE'],0),('flush-payload',L['COMMAND_BASE']+8+7,1)]:
        words,meta=compile_case(landing_fixture);words[field]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-landing-'+name,status=64))
    overflow=copy.deepcopy(next(c for c in cases if c['name']=='landing-all-2048-receipts'))
    overflow['effects'].append(dict(name='overflow',type='damage',source='스킬2',stat='damage',fixed_value=100,target='boss',trigger=dict(timing=['battle_start'],condition=[])));overflow['owners'].append(4)
    enemy_bad.append(compile_case(overflow));enemy_rejections.append(dict(name='landing-2049-receipts',status=64))
    overflow=copy.deepcopy(landing_fixture);next(e for e in overflow['effects'] if e['stat']=='lifesteal_pct')['fixed_value']=1e308
    enemy_bad.append(compile_case(overflow));enemy_rejections.append(dict(name='lifesteal-numeric-overflow',status=16))
    removal_base=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];removal_recipient=L['RECIPIENT_BASE']+8;removal_packet=L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']
    for name,fixture,field,value in [
        ('scope','removal-default-global',removal_base+21,3),
        ('unknown-name','removal-default-global',removal_base+18,256),
        ('invalid-name','removal-default-global',removal_base+18,0xfffffffe),
        ('global-audience','removal-default-global',removal_recipient,1),
        ('allied-enemy-selector','removal-target-self',removal_recipient,4),
        ('allied-flags','removal-target-self',removal_recipient+7,8),
        ('allied-packet','removal-target-self',removal_packet+1,1),
        ('enemy-route','removal-enemy-boss',removal_packet,10),
        ('enemy-count-zero','removal-enemy-boss',removal_packet+1,0),
        ('enemy-count-overflow','removal-enemy-boss',removal_packet+1,257),
        ('enemy-packet-payload','removal-enemy-boss',removal_packet+2,1)]:
        words,meta=compile_case(next(c for c in cases if c['name']==fixture));words[field]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-removal-'+name,status=64))
    extension_ally=next(c for c in cases if c['name']=='duration-extend-shared-instance-whole-expiry')
    extension_enemy=next(c for c in cases if c['name']=='duration-extend-enemy-independent-boss')
    extension_at=L['DEFINITION_BASE']+L['DEFINITION_WORDS']
    for label,fixture,offset,value in [
        ('policy-zero',extension_ally,extension_at+F['TARGET'],0),('policy-three',extension_ally,extension_at+F['TARGET'],3),
        ('infinite-value',extension_ally,extension_at+F['VALUE']+1,0x7ff00000),('nan-value',extension_ally,extension_at+F['VALUE']+1,0x7ff80000),
        ('recipient-flags',extension_ally,L['RECIPIENT_BASE']+8+7,1),('membership-padding',extension_ally,L['FORCE_BASE']+L['MASK_WORDS'],1<<31),
        ('ally-packet',extension_ally,L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS'],1),
        ('enemy-recipient',extension_enemy,L['RECIPIENT_BASE']+8,1),('enemy-route',extension_enemy,L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS'],10),
        ('enemy-count',extension_enemy,L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+1,0),('enemy-payload',extension_enemy,L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+2,1)]:
        words,meta=compile_case(fixture);words[offset]=value
        enemy_bad.append((words,meta));enemy_rejections.append(dict(name='wire-duration-extension-'+label,status=64))
    from portable_status_validation import rejection_programs as status_rejections
    status_bad,status_rejected=status_rejections(cases,compile_case)
    from portable_stack_validation import rejection_programs as stack_rejections
    stack_bad,stack_rejected=stack_rejections(cases,compile_case)
    from portable_protection_validation import rejection_programs as protection_rejections
    protection_bad,protection_rejected=protection_rejections(cases,compile_case)
    from portable_split_validation import rejection_programs as split_rejections
    split_bad,split_rejected=split_rejections(cases,compile_case)
    from portable_instant_list_validation import rejection_programs as instant_list_rejections
    instant_bad,instant_rejected=instant_list_rejections(cases,compile_case)
    from portable_named_state_validation import rejection_programs as named_state_rejections
    named_bad,named_rejected=named_state_rejections(cases,compile_case)
    rejections += enemy_rejections+stack_rejected+status_rejected+protection_rejected+split_rejected+instant_rejected+named_rejected;negative_programs += enemy_bad+stack_bad+status_bad+protection_bad+split_bad+instant_bad+named_bad
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
        if 'expected_source_queries' in c:contains(r['source_queries'],c['expected_source_queries'],c['name']+'.sources')
        if 'expected_resource_queries' in c:
            assert len(r['resource_queries'])==len(c['expected_resource_queries'])
            contains(r['resource_queries'],c['expected_resource_queries'],c['name']+'.resources')
        if 'expected_resource_trace' in c:assert r['resource_trace']==c['expected_resource_trace'],c['name']+'.resource_trace'
        if 'expected_packets' in c:
            assert len(r['trace'])==len(c['expected_packets']),c['name']+'.packet_count'
            contains(r['trace'],c['expected_packets'],c['name']+'.packets')
        if 'expected_target_scores' in c:contains(r['target_scored_damage'],c['expected_target_scores'],c['name']+'.target_scores')
        if 'expected_trace_total' in c:assert r['trace_total']==c['expected_trace_total'],c['name']
        if 'expected_targets' in c:contains(r['targets'],c['expected_targets'],c['name']+'.targets')
        if 'equivalent_computation_to' in c:
            reference=result['results'][next(i for i,x in enumerate(cases) if x['name']==c['equivalent_computation_to'])]
            assert {k:v for k,v in r.items() if k not in ('trace','burst_trace')}=={k:v for k,v in reference.items() if k not in ('trace','burst_trace')},c['name']
            assert r['trace']==[] and len(r['burst_trace'])>=c['minimum_burst_records'],c['name']
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
        if 'expected_bullet_lifetimes' in c:contains(r['bullet_lifetimes'],c['expected_bullet_lifetimes'],c['name']+'.bullet_lifetimes')
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
    reference=verify_trigger_reference([c for c in cases if not c.get('health_reference') and not c.get('capacity_reference') and not c.get('cover_reference') and not c.get('named_buff_reference') and not c.get('enemy_buff_reference')])
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
    from portable_bullet_oracle import observe as bullet_observe
    bullet_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('bullet_reference'):continue
        cpu=bullet_observe(case)
        expected=case.get('known_health_cpu_difference',{}).get('expected_queries',case['expected_queries'])
        contains(cpu['queries'],expected,case['name']+'.cpu')
        live=[x for x in gpu['carriers'] if x['active']]
        assert len(live)==len(cpu['carriers']),case['name']+'.cpu.carriers'
        contains(live,cpu['carriers'],case['name']+'.cpu.carriers')
        if 'known_health_cpu_difference' in case:
            health_differences.append(dict(name=case['name'],reason=case['known_health_cpu_difference']['reason'],actual_cpu_queries=cpu['queries'],expected_cpu_queries=expected,expected_gpu_queries=case['expected_queries']))
            health_reference.append(case['name'])
        else:contains(gpu['queries'],cpu['queries'],case['name']+'.gpu_vs_cpu')
        bullet_reference.append(case['name'])
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    from portable_burst_oracle import observe as burst_observe
    burst_reference=[];duration_reference=[];ammo_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not (case.get('burst_reference') or case.get('duration_reference') or case.get('ammo_reference')):continue
        cpu=burst_observe(case)
        contains(cpu['queries'],case['expected_queries'],case['name']+'.cpu')
        contains(gpu['queries'],cpu['queries'],case['name']+'.gpu_vs_cpu')
        if case['combat'].get('trace')!='summary':
            casts=[dict(time=b['time'],owner=b['owner'],stage=b['event'] if b['event']<7 else b['event']-6) for b in gpu['burst_trace'] if b['event'] in (1,2,3,7,8,9)]
            assert casts==cpu['casts'],(case['name'],casts,cpu['casts'])
        if case.get('ammo_reference'):ammo_reference.append(case['name'])
        elif case.get('duration_reference'):duration_reference.append(case['name'])
        else:burst_reference.append(case['name'])
    from portable_enemy_buff_oracle import observe as enemy_buff_observe
    enemy_buff_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('enemy_buff_reference'):continue
        cpu=enemy_buff_observe(case)
        contains(cpu,case['expected_queries'],case['name']+'.native_enemy_buff')
        contains(gpu['queries'],cpu,case['name']+'.enemy_buff_gpu_vs_cpu')
        enemy_buff_reference.append(case['name'])
    named_buff_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('named_buff_reference'):continue
        cpu=carrier_observe(case)
        contains(cpu,case['expected_queries'],case['name']+'.native_cpu')
        contains(gpu['queries'],cpu,case['name']+'.gpu_vs_cpu')
        named_buff_reference.append(case['name'])
    mode_reference=[];mode_differences=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('mode_session_reference'):continue
        cpu=burst_observe(case);projected=copy.deepcopy(cpu['queries']);known=case.get('known_mode_cpu_difference')
        if known:
            seen=set()
            for difference in known['differences']:
                query=difference['query'];path_parts=difference['path'];key=(query,tuple(path_parts));assert key not in seen;seen.add(key)
                native=cpu['queries'][query];actual=gpu['queries'][query];target=projected[query]
                for part in path_parts[:-1]:native=native[part];actual=actual[part];target=target[part]
                last=path_parts[-1]
                assert native[last]==difference['cpu'],(case['name'],'changed pinned CPU behavior',difference,native[last])
                assert actual[last]==difference['gpu'],(case['name'],'changed canonical behavior',difference,actual[last])
                target[last]=difference['gpu']
            mode_differences.append(dict(name=case['name'],reason=known['reason'],contract=known['contract'],differences=known['differences'],actual_cpu_queries=cpu['queries']))
        contains(projected,case['expected_queries'],case['name']+'.contract')
        contains(gpu['queries'],projected,case['name']+'.all-undeclared-cpu-fields')
        for who,expected in cpu.get('weapon_timings',{}).items():contains(gpu['weapons'][who],expected,case['name']+'.physical-warmup-clock')
        mode_reference.append(case['name'])
    from portable_enemy_oracle import observe as enemy_observe
    enemy_reference=[];staged_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('enemy_reference'):continue
        cpu=enemy_observe(case)
        contains(cpu['queries'],case['expected_queries'],case['name']+'.cpu_components')
        contains(gpu['queries'],cpu['queries'],case['name']+'.gpu_vs_cpu_components')
        contains(gpu['target_scored_damage'],cpu['target_scored_damage'],case['name']+'.target_scores')
        if case['combat'].get('trace','full')=='full':
            assert len(gpu['trace'])==len(cpu['packets']),case['name']+'.component_packets'
            contains(gpu['trace'],cpu['packets'],case['name']+'.component_packets')
        if case.get('staged_reference'):
            actual=sorted((x for x in gpu['staged_applications'] if x['active']),key=lambda x:x['definition'])
            assert actual==cpu['staged_state'],(case['name'],'staged state',actual,cpu['staged_state'])
            staged_reference.append(case['name'])
        enemy_reference.append(case['name'])
    from portable_health_oracle import observe as cover_observe
    cover_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('cover_reference'):continue
        cpu=cover_observe(case,with_cover=True)
        contains(cpu,case['expected_queries'],case['name']+'.cpu_cover')
        contains(gpu['queries'],cpu,case['name']+'.gpu_vs_cpu_cover')
        cover_reference.append(case['name'])
    from portable_pending_oracle import observe as pending_observe
    pending_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('pending_reference'):continue
        cpu=pending_observe(case)
        contains(cpu['queries'],case['expected_queries'],case['name']+'.cpu_pending')
        contains(gpu['queries'],cpu['queries'],case['name']+'.gpu_vs_cpu_pending')
        if case['combat'].get('trace','full')=='full':
            assert len(gpu['trace'])==len(cpu['packets']),case['name']+'.pending_packets'
            contains(gpu['trace'],cpu['packets'],case['name']+'.pending_packets')
        pending_reference.append(case['name'])
    from portable_resource_oracle import observe as resource_observe
    resource_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('resource_reference'):continue
        cpu=resource_observe(case)
        contains(cpu['queries'],case['expected_queries'],case['name']+'.native_resource')
        contains(cpu['resource_queries'],case['expected_resource_queries'],case['name']+'.native_resource_query')
        for key in ('resource_queries','resource_trace','resource_trace_total'):assert gpu[key]==cpu[key],(case['name'],key,gpu[key],cpu[key])
        resource_reference.append(case['name'])
    scale_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('scale_reference'):continue
        # Health/cover/weapon/enemy observers above compare their full exposed
        # state. Plain reference fixtures use the original resource manager.
        if not any(case.get(key) for key in ('health_reference','cover_reference','weapon_reference','enemy_reference')):
            cpu=resource_observe(case)
            contains(cpu['queries'],case['expected_queries'],case['name']+'.native_scale')
            contains(gpu['queries'],cpu['queries'],case['name']+'.gpu_vs_native_scale')
        scale_reference.append(case['name'])
    from portable_source_oracle import observe as source_observe
    source_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('source_reference'):continue
        if not (case.get('health_reference') or case.get('enemy_reference')):
            cpu=source_observe(case);contains(cpu['queries'],case['expected_queries'],case['name']+'.native_source')
            contains(gpu['queries'],cpu['queries'],case['name']+'.gpu_native_source')
            for key in ('source_queries','periodic_sources'):assert gpu[key]==cpu[key],(case['name'],key,gpu[key],cpu[key])
        source_reference.append(case['name'])
    from portable_lifesteal_oracle import observe as lifesteal_observe
    from portable_landing_oracle import observe as landing_observe
    lifesteal_reference=[];landing_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not (case.get('lifesteal_reference') or case.get('landing_reference')):continue
        native=(landing_observe if case.get('landing_reference') else lifesteal_observe)(case)
        contains(native['queries'],case['expected_queries'],case['name']+'.native_hand')
        contains(gpu['queries'],native['queries'],case['name']+'.native_receipts')
        if 'expected_landing_queue' in case:contains(gpu['landing_queue'],case['expected_landing_queue'],case['name']+'.queue')
        if 'expected_pending_burst' in case:contains(gpu['pending_burst'],case['expected_pending_burst'],case['name']+'.pending')
        (landing_reference if case.get('landing_reference') else lifesteal_reference).append(case['name'])
    from portable_removal_oracle import observe as removal_observe
    removal_reference=[]
    for case,gpu in zip(cases,result['results']):
        if not case.get('removal_reference'):continue
        cpu=removal_observe(case)
        contains(cpu['queries'],[{k:v for k,v in q.items() if k!='damage'} for q in case['expected_queries']],case['name']+'.native_hand')
        contains(gpu['queries'],cpu['queries'],case['name']+'.native_removal')
        def aggregate(rows):
            merged={}
            for r in rows:
                key=(r['definition'],r['stacks'],r['lazy_pending']);merged[key]=merged.get(key,0)|r['recipients']
            return sorted((definition,stacks,lazy,mask) for (definition,stacks,lazy),mask in merged.items())
        actual=[]
        for r in gpu['carriers']:
            if not r['active']:continue
            r=dict(r);e=case['effects'][r['definition']]
            if e['type']=='damage' and e.get('tick_interval'):
                binding=gpu['periodic_bindings'][r['definition']]
                r['recipients']=sum(1<<(target+5) for target in binding['target_order']) if binding['flags']&1 else 1<<(gpu['timers'][r['definition']]['target_slot']+5)
            actual.append(r)
        assert aggregate(actual)==aggregate(cpu['carriers']),(case['name'],'resident membership',aggregate(actual),aggregate(cpu['carriers']))
        clocks=[dict(definition=i,due=t['due'],expiry=t['expiry']) for i,t in enumerate(gpu['timers']) if t['active']]
        assert clocks==cpu['timers'],(case['name'],'clocks',clocks,cpu['timers'])
        for packet in cpu['packets']:
            assert any(t['effect']==packet['name'] and t['time']==packet['time'] and t['target_mask']==packet['target_mask'] for t in gpu['trace']),(case['name'],'native packet',packet,gpu['trace'])
        removal_reference.append(case['name'])
    from portable_duration_extend_oracle import compare as compare_extension
    duration_extend_reference=[]
    for case,gpu in zip(cases,result['results']):
        if case.get('duration_extend_reference'):
            compare_extension(case,gpu,contains);duration_extend_reference.append(case['name'])
    from portable_stack_oracle import compare as compare_stacks
    from portable_status_oracle import compare as compare_status
    from portable_protection_oracle import compare as compare_protection
    protection_reference=[]
    stack_reference=[];status_reference=[]
    for case,gpu in zip(cases,result['results']):
        if case.get('protection_reference') or case.get('split_reference'):
            compare_protection(case,gpu,contains);protection_reference.append(case['name'])
        elif case.get('status_reference'):
            compare_status(case,gpu,contains);status_reference.append(case['name'])
        elif case.get('stack_reference'):
            compare_stacks(case,gpu,contains);stack_reference.append(case['name'])
    from portable_instant_list_oracle import compare as compare_instant_lists
    instant_reference=[]
    for case,gpu in zip(cases,result['results']):
        if case.get('instant_list_reference'):
            compare_instant_lists(case,gpu,contains);instant_reference.append(case['name'])
    from portable_named_state_oracle import compare as compare_named_states
    named_state_reference=[]
    for case,gpu in zip(cases,result['results']):
        if case.get('named_state_reference'):
            compare_named_states(case,gpu,contains);named_state_reference.append(case['name'])
    result.update(named_state_cpu_regressions=named_state_reference,instant_list_cpu_regressions=instant_reference,protection_cpu_regressions=protection_reference,status_cpu_regressions=status_reference,stack_cpu_regressions=stack_reference,duration_extend_cpu_regressions=duration_extend_reference,removal_cpu_regressions=removal_reference,landing_cpu_regressions=landing_reference,lifesteal_cpu_regressions=lifesteal_reference,staged_cpu_regressions=staged_reference,source_cpu_regressions=source_reference,scale_reference_cpu_regressions=scale_reference,hit_reference_cpu_regressions=[c['name'] for c in cases if c.get('hit_reference')],resource_cpu_regressions=resource_reference,periodic_target_cpu_regressions=[c['name'] for c in cases if c.get('periodic_reference')],enemy_buff_cpu_regressions=enemy_buff_reference,named_buff_cpu_regressions=named_buff_reference,mode_session_cpu_regressions=mode_reference,known_mode_cpu_differences=mode_differences,ammo_instant_cpu_regressions=ammo_reference,burst_duration_cpu_regressions=duration_reference,pending_controller_cpu_regressions=pending_reference,cover_cpu_regressions=cover_reference,enemy_component_cpu_regressions=enemy_reference,burst_cpu_regressions=burst_reference,bullet_cpu_regressions=bullet_reference,lazy_cpu_regressions=[c['name'] for c in cases if c.get('lazy_reference')],carrier_cpu_regressions=carrier_reference,capacity_cpu_regressions=capacity_reference,health_cpu_regressions=health_reference,known_health_cpu_differences=health_differences,known_cpu_differences=cpu_differences,weapon_cpu_regressions=weapon_reference,damage_cpu_regressions=damage_reference,trigger_cpu_regressions=reference,passed=True,stage='verified',cases=rows,validation_sha256=hashes,cpu_trace_used_as_gpu_input=False,
                  rejection_execution=negative,rejected_cases=rejections,
                  scope='Shared event/combat mechanics, enemy packets, allied cover state and pending B3 bonuses; independent components are not full battle or catalog certification')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,cases=len(rows),device=result['transport']['device'],backend=args.backend)))


if __name__=='__main__':main()
