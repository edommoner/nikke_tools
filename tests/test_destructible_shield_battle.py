"""Actual native scheduler contracts before the shared Frame routing port."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline,buff_manager
from destructible_shield_policy import BOSS,select
from destructible_battle_runtime import typed_battle
from destructible_shield_battle_cases import fixtures
from portable_destructible_shield_battle_contracts import verify
from world_destructible_shield_battle_native import observe
from impact_specs import ActorHandle,ActorKind

class ShieldBattleTests(unittest.TestCase):
    def test_fifteen_literal_battles(self):
        self.assertEqual(len(fixtures()),15)
        for case in fixtures():
            with self.subTest(name=case['name']):self.assertTrue(verify(case,observe(case)[0])['reference_model_gap'])

    def test_explicit_owner_and_declared_model_required(self):
        for owner in (True,[0,0,1],ActorHandle(ActorKind.BODY,1),ActorHandle(ActorKind.BODY,0,2),ActorHandle(ActorKind.ADD,0)):
            with self.subTest(owner=owner),self.assertRaisesRegex(ValueError,'explicit canonical boss'):
                with typed_battle(fixtures()[0]['typed_bindings'],modifier_model=True,shield_owner=owner):pass
        with self.assertRaisesRegex(ValueError,'declared modifier model'):
            with typed_battle(fixtures()[0]['typed_bindings'],shield_owner=BOSS):pass

    def test_active_clock_and_generation_owned_selection(self):
        from destructible_world_runtime import DestructibleWorld
        world=DestructibleWorld([dict(id='idle',until=dict(time=1.))],[dict(node='idle',kind=3,identity=10,capacity=10.,owner=[0,0,1])])
        with self.assertRaisesRegex(ValueError,'active battle'):select(world,BOSS)
        world.advance(0.)
        self.assertEqual(select(world,BOSS),(0,ActorHandle(ActorKind.HP_SHIELD,10)))
        world.finish(1.)
        with self.assertRaisesRegex(ValueError,'active battle'):select(world,BOSS)

    def test_unsupported_skill_does_not_silently_bypass_on_empty_shield_set(self):
        for live in (True,False):
            c=copy.deepcopy(fixtures()[0]);c['effects'][1]['damage_count']=2
            if not live:c['typed_bindings'][0].pop('owner')
            with self.subTest(live=live),self.assertRaisesRegex(ValueError,'Plain all_projectiles'):observe(c)

    def test_exception_restores_handler_and_scalar_scope(self):
        before=(timeline.BuffManager,timeline.calc_damage,timeline.simulate,timeline.HitEvent,buff_manager.BuffManager.register_damage_handler,dict(buff_manager._STAT_TO_BUFF))
        with patch('destructible_damage_policy.calculate',side_effect=RuntimeError('shield scalar failure')):
            with self.assertRaisesRegex(RuntimeError,'shield scalar failure'):observe(fixtures()[0])
        self.assertEqual(before,(timeline.BuffManager,timeline.calc_damage,timeline.simulate,timeline.HitEvent,buff_manager.BuffManager.register_damage_handler,dict(buff_manager._STAT_TO_BUFF)))
        verify(fixtures()[0],observe(fixtures()[0])[0])

    def test_common_reference_cli_retains_model_gap(self):
        from portable_reference import REFERENCES
        self.assertEqual(REFERENCES['destructible-shield-battle'][0],'destructible_shield_battle_cases')
        answer=verify(fixtures()[0],observe(fixtures()[0])[0])
        self.assertFalse(answer['gpu_connected']);self.assertFalse(answer['in_game_rules_verified'])

if __name__=='__main__':unittest.main()
