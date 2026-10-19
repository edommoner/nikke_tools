import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
import engine_worker
from portable_runtime import compile_program,UnsupportedPortable
from portable_specs import check_schema,LIMITS
from timer_registry_cases import cases,prepare,NAMES


class PortableBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
        self.effects=prepare(next(cases()))._effects
        self.script=[[0,0,0,0,0,-1,0,0],[1,2,0,0,-1,0,0,0]]

    def compile(self):
        return compile_program(self.chars,self.effects,self.script,[1000]*5)

    def test_existing_authored_definitions_compile_without_mutation(self):
        before=copy.deepcopy((self.chars,self.effects,self.script))
        check_schema();program,meta=self.compile()
        self.assertEqual(len(program),LIMITS['INPUT_WORDS'])
        self.assertEqual(meta['effects'],['no critical','clock'])
        self.assertEqual((self.chars,self.effects,self.script),before)

    def test_unported_semantics_fail_before_any_gpu_dispatch(self):
        variants=[dict(trigger=dict(timing=['passive'],condition=['has_burst1_ally'])),dict(stat='taunt'),dict(target='allies_random:1'),dict(scaling='stack_count'),
                  dict(trigger=dict(timing=['battle_start'],condition=['full_burst'])),
                  dict(trigger=dict(timing=['event:enemy_spawn'],condition=[])),
                  dict(trigger=dict(timing=['battle_start'],condition=['self_stun_immune']))]
        for change in variants:
            with self.subTest(change=change):
                saved=self.effects;self.effects=copy.deepcopy(saved)
                self.effects[0][0].update(change)
                with self.assertRaises(UnsupportedPortable):self.compile()
                self.effects=saved
        self.effects.append(copy.deepcopy(self.effects[0]))
        program,metadata=self.compile()
        self.assertEqual(program[1],len(self.effects))
        self.assertEqual(len(metadata['effects']),len(self.effects))

    def test_descriptor_boundaries_fail_before_gpu(self):
        from portable_trigger_specs import validate_input
        validate_input(dict(trigger=dict(timing=['battle_start']*8,condition=['during_full_burst']*3)))
        for trigger in (dict(timing=['battle_start']*9),dict(timing=[]),
                        dict(timing=['battle_start'],condition=['during_full_burst']*4),
                        dict(timing=['every:0s']),dict(timing=['every:nan']),
                        dict(timing=['every:inf']),dict(timing=['event:enemy_spawn']),
                        dict(timing=['battle_start'],condition=['self_stun_immune'])):
            with self.subTest(trigger=trigger),self.assertRaises(ValueError):validate_input(dict(trigger=trigger))

    def test_quantity_metadata_and_policy_are_fail_closed(self):
        from portable_runtime import validate_effect
        base=dict(name='quantity',source='스킬1',type='buff',stat='max_ammo_pct',fixed_value=10,
                  duration=-1,target='self',trigger=dict(timing=['battle_start'],condition=[]))
        for patch in (dict(_quant_group={}),dict(_source_tag=[]),dict(max_ammo_reduction_exclusive=1),
                      dict(stat='atk_pct',max_ammo_reduction_exclusive=True)):
            with self.subTest(patch=patch),self.assertRaises(ValueError):validate_effect({**base,**patch},combat={})
        for patch in (dict(stat='charge_time_fixed',fixed_value=-1),dict(stat='charge_time_fixed',values={'10':.2})):
            with self.subTest(patch=patch),self.assertRaises(ValueError):validate_effect({**base,**patch},combat={})

    def test_time_dimensions_and_discrete_ranges_are_checked(self):
        for script in ([[1,0,0,0,0,-1,0,0],[0,2,0,0,-1,0,0,0]],
                       [[float('nan'),0,0,0,0,-1,0,0]],
                       [[0,2,0,0,-1,64,0,0]],[[0,0,0,5,0,-1,0,0]],
                       [[0,18,0,0,-1,-1,float('inf'),0]]):
            with self.subTest(script=script),self.assertRaises(ValueError):
                compile_program(self.chars,self.effects,script,[1000]*5)
        for maximum in (0,1.5,True,2**31):
            self.effects[0][0]['max_stack']=maximum
            with self.subTest(maximum=maximum),self.assertRaises(ValueError):self.compile()




class PortableHealthInputTests(unittest.TestCase):
    def test_initial_state_rejects_precomputed_or_invalid_health(self):
        import copy
        from portable_runtime import compile_program
        import engine_worker
        from timer_registry_cases import NAMES
        chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
        effect=dict(name='noop',source='스킬1',type='buff',stat='atk_pct',fixed_value=0,target='self',duration=-1,trigger=dict(timing=['battle_start'],condition=[]))
        for patch in ({'base_hp':0},{'base_hp':True},{'base_hp':float('inf')},{'hp':-1},{'base_hp':100,'hp':101},{'base_defense':-1},{'max_hp':2000}):
            allies=[dict(base_hp=1000,hp=500) for _ in range(5)];allies[0].update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):compile_program(chars,[(effect,NAMES[0])],[[0,2,0,0,-1,0,0,0]],[1000]*5,allies=allies)


class PortableHPEdgeInputTests(unittest.TestCase):
    def test_invalid_hp_edge_thresholds_and_counts_fail_before_gpu(self):
        from portable_trigger_specs import validate_input
        for timing in ('hp_below:nan','hp_below:inf','hp_below_count:50:0','hp_below_count:50:-1','hp_below_count:50:2.5','event:adjacent_hp_below:nan'):
            with self.subTest(timing=timing),self.assertRaises(ValueError):validate_input(dict(trigger=dict(timing=[timing],condition=[])))

    def test_callers_cannot_inject_hp_edge_history_as_external_notifications(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('hp_edge_verify',ROOT/'scripts/verify-portable-combat.py')
        v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        for event in (31,48,32,37,38,46):
            case=copy.deepcopy(v.fixtures()[0]);case['script']=[[0,0,event,0,0,-1,0,0]]
            with self.subTest(event=event),self.assertRaises(ValueError):v.compile_case(case)


class PortableIncomingInputTests(unittest.TestCase):
    def test_incoming_attack_fields_are_typed_raw_inputs(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('incoming_verify',ROOT/'scripts/verify-portable-combat.py')
        v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        base=copy.deepcopy(v.fixtures()[0])
        for command in ([0,25,0,0,0,-1,300,100],[0,25,0,0,32,-1,300,100],
                        [0,25,0,1,1,-1,300,100],[0,25,1,0,1,-1,300,100],
                        [0,25,0,0,True,-1,300,100],[0,25,0,0,1,-1,True,100],
                        [0,25,0,0,1,-1,300,float('inf')],[0,25,0,0,1,-1,-1,100],
                        [0,25,0,0,1,-1,300,-1],[0,25,0,0,1,0,300,100]):
            case=copy.deepcopy(base);case['script']=[command]
            with self.subTest(command=command),self.assertRaises(ValueError):v.compile_case(case)

class PortableRecipientInputTests(unittest.TestCase):
    def test_unported_random_recipient_leaves_remain_fail_closed(self):
        from portable_runtime import validate_effect
        effect=dict(name='recipient',type='buff',stat='atk_pct',fixed_value=10,
                    target='self',trigger=dict(timing=['battle_start'],condition=[]))
        for target in ('allies_random:2',['self','allies_random:2']):
            with self.subTest(target=target),self.assertRaises(UnsupportedPortable):
                validate_effect({**effect,'target':target},combat={})

    def test_burst_recipient_needs_gpu_combat_state(self):
        from portable_runtime import validate_effect
        effect=dict(name='heal',type='instant',stat='heal_hp_pct',fixed_value=10,
                    trigger=dict(timing=['battle_start'],condition=[]))
        for target in ('all_allies_burst_casted','all_allies_burst_not_casted','allies_burst_casted_weapon:MG'):
            with self.subTest(target=target),self.assertRaises(UnsupportedPortable):
                validate_effect({**effect,'target':target})

    def test_malformed_recipient_counts_do_not_silently_truncate(self):
        from portable_runtime import validate_effect
        effect=dict(name='heal',type='instant',stat='heal_hp_pct',fixed_value=10,
                    trigger=dict(timing=['battle_start'],condition=[]))
        for target in ('allies_lowest_hp:0','allies_top_atk:6','allies_right:-1',
                       'allies_adjacent:1.5','allies_class:화력형:6','allies_top_base_charge_time:NaN'):
            with self.subTest(target=target),self.assertRaises(UnsupportedPortable):
                validate_effect({**effect,'target':target})


class PortableBulletInputTests(unittest.TestCase):
    def test_bullet_lifetime_requires_discrete_positive_count_or_unbounded(self):
        from portable_runtime import validate_effect
        effect=dict(name='bullet',type='buff',stat='atk_pct',fixed_value=10,
                    target='self',trigger=dict(timing=['battle_start'],condition=[]))
        for count in (True,False,0,-2,1.5,2**31,None):
            with self.subTest(count=count),self.assertRaises(UnsupportedPortable):
                validate_effect({**effect,'duration_bullets':count},combat={})
        for count in (1,2**31-1,-1):validate_effect({**effect,'duration_bullets':count},combat={})
        with self.assertRaises(UnsupportedPortable):validate_effect({**effect,'duration_bullets':1})


class PortableBurstAdmissionTests(unittest.TestCase):
    def test_burst_effects_require_combat_and_ally_recipient(self):
        from portable_runtime import validate_effect
        for kind,stat in [('buff','burst_cooldown'),('instant','burst_cooldown_reduce'),('instant','burst_charge_pct')]:
            effect=dict(name=stat,type=kind,stat=stat,fixed_value=5,target='all_allies',trigger=dict(timing=['battle_start'],condition=[]))
            with self.subTest(stat=stat):
                validate_effect(effect,combat={})
                with self.assertRaises(ValueError):validate_effect(effect)
                with self.assertRaises(ValueError):validate_effect({**effect,'target':'boss'},combat={})


class PortableEnemyAdmissionTests(unittest.TestCase):
    def test_damage_counts_and_target_semantics_are_not_discarded(self):
        from portable_runtime import validate_effect
        e=dict(name='test',type='damage',stat='damage',fixed_value=100,target='all_enemies',trigger=dict(timing=['on_attack'],condition=[]))
        for stat in ('damage:1','damage:256','split_damage:3','damage:state'):
            validate_effect({**e,'stat':stat},combat={})
        for patch in (dict(stat='damage:-1'),dict(stat='damage:257'),dict(stat=None),dict(target='enemies_random:1'),dict(target='enemies_top_atk:0')):
            with self.subTest(patch=patch),self.assertRaises(ValueError):validate_effect({**e,**patch},combat={})
        with self.assertRaises(ValueError):validate_effect(e)


        periodic={**e,'tick_interval':.25,'duration':1};validate_effect(periodic,combat={})
        from portable_periodic_specs import periodic_flags
        self.assertEqual(periodic_flags(periodic,0)&1,1)


class PortableRealInputTests(unittest.TestCase):
    def test_complete_real_preparation_is_preserved_and_policies_fail_closed(self):
        from detail_coverage import body_for
        from portable_roster_input import compile_static_battle
        body={**body_for(['미란다','도라','드레이크','N102','메어리']),'burst_gauge_mode':'accumulate','_portable_static_inputs':True}
        prepared=engine_worker.evaluate(body);before=copy.deepcopy(prepared)
        words,metadata=compile_static_battle(prepared)
        self.assertEqual(words[1],len(prepared['effects']));self.assertEqual(words[6],1)
        self.assertEqual(metadata['effects'],[x['effect']['name'] for x in prepared['effects']])
        self.assertEqual(prepared,before)
        for patch in ('fixed','controls','world'):
            bad=copy.deepcopy(prepared)
            if patch=='fixed':bad['policies']['config']['burst_gauge_mode']='fixed'
            elif patch=='controls':bad['policies']['controls']['미란다']={'tap_fire':True}
            else:bad['enemy']['has_parts']=True
            with self.subTest(patch=patch),self.assertRaises(UnsupportedPortable):compile_static_battle(bad)


class PortableCoverInputTests(unittest.TestCase):
    def test_unported_cover_basis_and_random_targets_remain_rejected(self):
        from portable_runtime import validate_effect
        effect=dict(name='cover',type='buff',stat='cover_hp_pct',fixed_value=10,target='self',trigger=dict(timing=['battle_start'],condition=[]))
        validate_effect({**effect,'scaling':'max_hp'})
        for patch in (dict(scaling='lost_hp_pct'),dict(target='allies_broken_cover_random:2')):
            with self.subTest(patch=patch),self.assertRaises(UnsupportedPortable):validate_effect({**effect,**patch})

    def test_cover_health_and_damage_are_typed_layer_inputs(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('cover_verify',ROOT/'scripts/verify-portable-combat.py')
        v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        base=copy.deepcopy(next(c for c in v.fixtures() if c.get('cover_reference')))
        for patch in (dict(base_cover_hp=0),dict(base_cover_hp=True),dict(cover_hp=-1),dict(cover_hp=1001),dict(cover_hp=float('nan'))):
            c=copy.deepcopy(base);c['environment']['allies'][0].update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):v.compile_case(c)
        for patch in (dict(cover_sync=1),dict(cover_sync='auto')):
            c=copy.deepcopy(base);c['environment'].update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):v.compile_case(c)
        for command in ([0,26,0,0,0,-1,100,0],[0,26,0,0,32,-1,100,0],[0,26,0,1,1,-1,100,0],[0,26,0,0,1,-1,-1,0],[0,26,0,0,1,-1,True,0],[0,26,0,0,1,-1,100,1]):
            c=copy.deepcopy(base);c['script']=[command]
            with self.subTest(command=command),self.assertRaises(ValueError):v.compile_case(c)


class PortablePendingInputTests(unittest.TestCase):
    def test_pending_and_ordinary_bonus_are_distinguished(self):
        import importlib.util
        from portable_specs import LIMITS as L
        spec=importlib.util.spec_from_file_location('pending_verify',ROOT/'scripts/verify-portable-combat.py')
        v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        case=copy.deepcopy(next(c for c in v.fixtures() if c['name']=='pending-later-burst-buff-excluded'))
        words,_=v.compile_case(case);at=L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']
        self.assertEqual(words[at+6:at+8],[1,1]);self.assertEqual(words[L['PENDING_EXCLUDE_BASE']+L['MASK_WORDS']],1<<2)
        case['effects'][1]['stat']='bonus_damage:3';words,_=v.compile_case(case)
        self.assertEqual(words[at+6:at+8],[0,0])
        case['effects'][1]['stat']='bonus_damage';case.pop('combat')
        with self.assertRaises(UnsupportedPortable):v.compile_case(case)

    def test_named_parent_must_resolve_for_the_same_caster(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('named_verify',ROOT/'scripts/verify-portable-combat.py')
        v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        case=next(c for c in v.fixtures() if c['name']=='pending-named-parent-static-repeat')
        for patch in ('missing','foreign','duplicate','dynamic'):
            bad=copy.deepcopy(case)
            if patch=='missing':bad['effects'][2]['target']='same_target:missing'
            elif patch=='foreign':bad['owners'][1]=1
            elif patch=='duplicate':bad['effects'].append(copy.deepcopy(bad['effects'][1]));bad['owners'].append(2)
            else:bad['effects'][1]['stat']='sequential_damage:state'
            with self.subTest(patch=patch),self.assertRaises(ValueError):v.compile_case(bad)


class PortableDurationInputTests(unittest.TestCase):
    def test_duration_requires_controller_and_preserves_source_identity(self):
        import importlib.util
        from portable_specs import LIMITS as L
        spec=importlib.util.spec_from_file_location('duration_verify',ROOT/'scripts/verify-portable-combat.py')
        v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        case=copy.deepcopy(next(c for c in v.fixtures() if c['name']=='duration-source-is-part-of-identity'))
        words,_=v.compile_case(case);at=L['DURATION_DEFINITION_BASE']
        self.assertEqual(words[at+2:at+6],[1,1,2,1])
        case.pop('combat')
        with self.assertRaises(UnsupportedPortable):v.compile_case(case)


if __name__=='__main__':unittest.main()


class PortableAmmoInputTests(unittest.TestCase):
    def test_ammo_requires_controller_and_real_recipients(self):
        from portable_runtime import validate_effect
        for stat in ('ammo_charge_pct','ammo_charge_flat'):
            e=dict(name='ammo',source='스킬1',type='instant',stat=stat,fixed_value=2,target='self',trigger=dict(timing=['on_attack'],condition=[]))
            with self.assertRaises(UnsupportedPortable):validate_effect(e)
            validate_effect(e,combat={})
            with self.assertRaises(UnsupportedPortable):validate_effect(dict(e,target='enemy'),combat={})

    def test_named_events_keep_reserved_builtin_semantics(self):
        from portable_trigger_specs import validate_input
        validate_input(dict(trigger=dict(timing=['event:custom cartridge completion'],condition=[])))
        for value in ('event:', 'event:enemy_spawn', 'event:enemy_spawn', 'event:foo:bar'):
            with self.subTest(value=value),self.assertRaises(ValueError):validate_input(dict(trigger=dict(timing=[value],condition=[])))
