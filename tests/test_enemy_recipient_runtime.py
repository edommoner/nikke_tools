"""Shared sparse bindings; no character-specific state matrix."""
import sys,unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_recipient_specs import EnemyRecipient,EnemyRecipients,logical_enemy
from impact_specs import ActorHandle
from enemy_recipient_cases import exercise,prepare,NAMES
from effect_runtime import state


class EnemyRecipientTests(unittest.TestCase):
    def gpu_program(self):
        from detail_coverage import a
        from detail_gpu import compile_effects
        from detail_boss import compile_world
        from enemy_recipient_cases import world_patterns
        bm,*_=prepare();chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES]
        program=compile_effects(chars,bm._effects,enemy_fields=True);raw=world_patterns()
        program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
        return bm,program

    def test_gpu_scope_policy_and_unconnected_lifetimes_fail_before_cuda(self):
        import copy
        from enemy_recipient_specs import specialize_static_fields
        from detail_gpu import run
        bm,program=self.gpu_program()
        rows=copy.deepcopy(program['effects']);original=copy.deepcopy(rows)
        self.assertEqual(specialize_static_fields(rows,has_add_sources=True),0)
        self.assertEqual(rows,original) # Configured delayed waves retain their recipient binding.
        self.assertGreater(specialize_static_fields(rows,has_add_sources=False),0)
        self.assertEqual(specialize_static_fields(rows,has_add_sources=False),0)
        with self.assertRaises(ValueError):specialize_static_fields(rows,has_add_sources=0)
        script=[[0,15,0,0,0,-1,0,0],[.01,2,135,0,5,0,12,1],[.1,5,0,0,0,-1,0,0]]
        self.assertEqual(program['effects'][0][48],1)
        for at,value in ((48,0),(48,4),(48,1.5),(62,1),(59,.1)):
            bad=copy.deepcopy(program);bad['effects'][0][at]=value
            with self.subTest(at=at,value=value),self.assertRaises(ValueError):run(None,[bad],script,[[0,0]],[bm.state['base_stats']])

    def test_targeted_notifications_and_queries_reject_invalid_descriptors(self):
        from detail_gpu import run
        bm,program=self.gpu_program()
        for row in ([.01,16,58,0,5,1,0,0],[.01,16,8,0,2,1,0,0],[.01,16,8,0,5,0,0,0],[.01,2,135,0,5,0,63,1],[.01,2,135,0,5,0,12,0]):
            script=[[0,15,0,0,0,-1,0,0],row,[.1,5,0,0,0,-1,0,0]]
            if row[1]!=2:script.insert(2,[.02,2,135,0,5,0,12,1])
            with self.subTest(row=row),self.assertRaises(ValueError):run(None,[program],script,[[0,0]],[bm.state['base_stats']])

    def test_refresh_generation_aliases_query_isolation_and_real_pool_death(self):
        self.assertTrue(exercise()['passed'])

    def test_overlapping_sets_have_independent_refresh_expiry_and_one_budget_charge(self):
        from enemy_fanout_cases import exercise as fanout,selector_exercise,order_exercise
        self.assertTrue(fanout()['passed'])
        self.assertTrue(selector_exercise()['passed']);self.assertTrue(selector_exercise(True)['passed'])
        self.assertTrue(order_exercise()['passed'])

    def test_fanout_snapshot_and_exception_restore(self):
        from enemy_fanout_cases import prepare as prepare_fanout
        from enemy_recipient_runtime import apply_receivers,key_for
        bm,boss,enemy,effect=prepare_fanout();boss.begin_frame(0,enemy)
        labels=[a.id for a in boss._runs[0].adds];seen=[]
        def apply(eff,targets):
            seen.append(key_for(bm,targets).bindings[0].actor)
            if len(seen)==1:boss.begin_frame(.3,enemy)
        apply_receivers(bm,effect,labels,apply)
        self.assertEqual([a.generation for a in seen],[1,1])
        self.assertEqual([key_for(bm,[label]).bindings[0].actor.generation for label in labels],[2,2])
        def fail(*args):raise ValueError('recipient witness')
        with self.assertRaisesRegex(ValueError,'recipient witness'):apply_receivers(bm,effect,labels,fail)
        self.assertEqual(state(bm).enemy_activation_stack,[])

    def test_receiver_mutations_and_old_immunity_do_not_cross_generations(self):
        from enemy_mutation_cases import exercise as mutations
        self.assertTrue(mutations()['passed'])

    def test_current_target_aliases_share_captured_recipient_for_fields_and_mutations(self):
        from enemy_recipient_specs import CURRENT_TARGETS
        from impact_specs import EventFrame
        bm,boss,enemy,registry=prepare();boss.begin_frame(0,enemy)
        runtime=state(bm);runtime.event_stack.append(EventFrame('hit_count',NAMES[0],0,target=ActorHandle(5,1)))
        expected=[boss._runs[0].adds[1].id]
        try:
            for target in CURRENT_TARGETS:
                with self.subTest(target=target):
                    self.assertEqual(bm.resolve_enemy_field_target({'type':'buff','stat':'received_dmg_pct'},target,NAMES[0]),expected)
                    self.assertEqual(bm.resolve_enemy_mutation({'target':target},NAMES[0]),expected)
        finally:runtime.event_stack.pop()

    def test_mutation_policies_and_periodic_binding_reject_before_cuda(self):
        from enemy_mutation_cases import prepare as mutation_manager,world_patterns
        from detail_coverage import a
        from detail_gpu import compile_effects
        from enemy_recipient_specs import validate_gpu_fields,mutation_instruction
        import copy
        bm,*_=mutation_manager();chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES]
        rows=compile_effects(chars,bm._effects,enemy_fields=True)['effects']
        validate_gpu_fields(rows,True)
        at=next(i for i,r in enumerate(rows) if mutation_instruction(r))
        for column,value in ((48,0),(48,4),(48,1.5)):
            bad=copy.deepcopy(rows);bad[at][column]=value
            with self.subTest(column=column,value=value),self.assertRaises(ValueError):validate_gpu_fields(bad,True)
        bad=copy.deepcopy(rows);bad[at][59]=.1;bad[at][258]=0
        with self.assertRaises(ValueError):validate_gpu_fields(bad,True)

    def test_immutable_distinct_bindings_and_explicit_actor_policy(self):
        from enemy_recipient_runtime import key_for
        a=EnemyRecipient('add',ActorHandle(5,0,2));key=EnemyRecipients((a,))
        self.assertEqual(key.actor_for('add'),ActorHandle(5,0,2));self.assertIsNone(key.actor_for('other'))
        self.assertEqual(logical_enemy(ActorHandle(1,7,4)),ActorHandle(0,0,1))
        bm,*_=prepare();self.assertEqual(len(key_for(bm,['__enemy__','__enemy__']).bindings),1)
        with self.assertRaises(FrozenInstanceError):a.actor=ActorHandle(5,0,3)
        for thunk in (lambda:EnemyRecipients(()),lambda:EnemyRecipients((a,a)),lambda:EnemyRecipient('part',ActorHandle(1,0)),lambda:logical_enemy(ActorHandle(2,0))):
            with self.assertRaises(ValueError):thunk()

    def test_stale_event_rejects_and_query_failures_restore_scope(self):
        from unittest.mock import patch
        from calculator.buff_manager import BuffManager
        bm,boss,enemy,registry=prepare();boss.begin_frame(0,enemy)
        bm.notify('hit_count',.01,NAMES[0],target_context=ActorHandle(5,0,1))
        boss.begin_frame(.3,enemy)
        with self.assertRaisesRegex(ValueError,'Stale'):bm.notify('hit_count',.31,NAMES[0],target_context=ActorHandle(5,0,1))
        self.assertEqual(state(bm).event_stack,[])
        with patch.object(BuffManager,'_build_plan',side_effect=ValueError('query witness')):
            with self.assertRaisesRegex(ValueError,'query witness'):bm.get_buffs(NAMES[0],boss._runs[0].adds[0].id,.32)
        self.assertEqual(state(bm).enemy_query_stack,[])
