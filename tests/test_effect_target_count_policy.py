"""Named target count reuses carrier lifetimes without changing normal readers."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
from test_target_counter_runtime import manager,NAMES
from portable_heavyarms_lock_cases import source_definitions
from calculator import buff_manager
from effect_target_count_policy import query,validate_effect,MODEL,STAT


class EffectTargetCountPolicyTests(unittest.TestCase):
    def effect(self,**changes):
        e=copy.deepcopy(source_definitions()[20]);e.update(changes);return e
    def activate(self,effect=None,t=1.):
        bm=manager([self.effect() if effect is None else effect]);bm._activate(bm._effects[0][0],NAMES[0],t);return bm
    def q(self,bm,who=0,name='록 온',t=1.1,**changes):
        args=dict(base_count=5,capacity_limit=128,model=MODEL);args.update(changes)
        return query(bm,NAMES[who],name,t,**args)
    def test_registered_cpu_contract_keeps_default_admission_closed(self):
        from portable_reference import REFERENCES
        from portable_readiness_semantics import reference_readiness
        from portable_model_gap_audit import verify
        self.assertIn('heavyarms-target-count-native',REFERENCES)
        r=reference_readiness(dict(phase='effect',kind='buff',stat=STAT,target='self',scaling=None))
        self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported'])
        self.assertEqual(r['declared_target_count_query']['cases'],4);self.assertFalse(r['declared_target_count_query']['selection_consumer_connected'])
        r=verify(ROOT)['missing_stats'][STAT]
        self.assertFalse(r['required_consumer_contract']['implementation_verified']);self.assertFalse(r['declared_query_reader']['gpu_supported'])
    def test_original_modifier_adds_ten_targets_and_two_shots_remove_it(self):
        bm=self.activate();self.assertEqual(self.q(bm)['capacity'],15)
        bm.consume_bullet_buffs(NAMES[0],2.);self.assertEqual(self.q(bm,t=2.1)['capacity'],15)
        bm.consume_bullet_buffs(NAMES[0],3.);self.assertEqual(self.q(bm,t=3.1)['capacity'],5)
    def test_activation_same_frame_and_other_caster_shots_keep_native_rules(self):
        bm=self.activate();bm.consume_bullet_buffs(NAMES[0],1.);self.assertEqual(self.q(bm)['capacity'],15)
        bm.consume_bullet_buffs(NAMES[1],2.);self.assertEqual(self.q(bm,t=2.1)['capacity'],15)
        bm.consume_bullet_buffs(NAMES[0],3.);self.assertEqual(self.q(bm,t=3.1)['capacity'],15)
        bm.consume_bullet_buffs(NAMES[0],4.);self.assertEqual(self.q(bm,t=4.1)['capacity'],5)
    def test_name_and_allied_recipient_are_independent(self):
        bm=self.activate();self.assertEqual(self.q(bm,name='other')['capacity'],5);self.assertEqual(self.q(bm,who=1)['capacity'],5)
        bm=self.activate(self.effect(target='all_allies'));self.assertEqual(self.q(bm,who=1)['capacity'],15)
        for t in (2.,3.):bm.consume_bullet_buffs(NAMES[1],t)
        self.assertEqual(self.q(bm,who=1,t=3.1)['capacity'],5);self.assertEqual(self.q(bm,t=3.1)['capacity'],15)
    def test_normal_readers_caches_global_maps_and_carriers_remain_unchanged(self):
        bm=self.activate();plain=bm.get_buffs(NAMES[0],'__enemy__',1.1)
        before=(dict(bm._plan_cache),copy.deepcopy(bm._buffs_cache),copy.deepcopy(bm._active),copy.deepcopy(bm.state))
        methods=(buff_manager.BuffManager.get_buffs,buff_manager.BuffManager._plan_step)
        maps=(dict(buff_manager._STAT_TO_BUFF),dict(buff_manager._BUFFS_ZERO))
        self.assertNotIn(STAT,plain);self.assertEqual(self.q(bm)['capacity'],15)
        self.assertEqual(before,(bm._plan_cache,bm._buffs_cache,bm._active,bm.state));self.assertEqual(plain,bm.get_buffs(NAMES[0],'__enemy__',1.1))
        self.assertEqual(methods,(buff_manager.BuffManager.get_buffs,buff_manager.BuffManager._plan_step));self.assertEqual(maps,(buff_manager._STAT_TO_BUFF,buff_manager._BUFFS_ZERO))
    def test_exact_expiry_and_refresh_use_native_carrier_state(self):
        bm=self.activate(self.effect(duration=.5,duration_bullets=-1))
        self.assertEqual(self.q(bm,t=1.49)['capacity'],15);self.assertEqual(self.q(bm,t=1.5)['capacity'],5)
        bm._activate(bm._effects[0][0],NAMES[0],1.5);self.assertEqual(self.q(bm,t=1.6)['capacity'],15)
    def test_unsupported_modifiers_and_out_of_capacity_results_fail_closed(self):
        for change in (dict(target='boss'),dict(scaling='max_ammo'),dict(fixed_value=True),dict(fixed_value=1.5),dict(fixed_value=-1),dict(fixed_value=float('inf')),dict(target_effect='')):
            with self.subTest(change=change),self.assertRaises(ValueError):validate_effect(self.effect(**change))
        bm=self.activate()
        for change in (dict(capacity_limit=14),dict(base_count=True),dict(capacity_limit=1<<31),dict(model='implicit')):
            with self.subTest(change=change),self.assertRaises(ValueError):self.q(bm,**change)
    def test_no_modifier_is_zero_and_unrelated_bad_stat_is_not_queried(self):
        bad=dict(type='buff',stat='atk_pct',target='self',name='unrelated',fixed_value=float('nan'),duration=-1,trigger=dict(timing=['battle_start'],condition=[]))
        bm=manager([bad]);bm._activate(bm._effects[0][0],NAMES[0],1.)
        self.assertEqual(self.q(bm)['capacity'],5)
    def test_changed_native_consumer_or_unreviewed_reader_requires_review(self):
        bm=self.activate()
        with patch.dict(buff_manager._STAT_TO_BUFF,{STAT:STAT}):
            with self.assertRaisesRegex(ValueError,'consumer changed'):self.q(bm)
        class Changed(type(bm)):
            def get_buffs(self,*a,**kw):return super().get_buffs(*a,**kw)
        bm.__class__=Changed
        with self.assertRaisesRegex(ValueError,'Unreviewed'):self.q(bm)
    def test_composes_with_existing_declared_modifier_query_class(self):
        from destructible_damage_policy import manager_type
        seed=manager([]);cls=manager_type(type(seed));bm=cls(seed.squad,state=copy.deepcopy(seed.state))
        bm._effects=[(self.effect(),NAMES[0])];bm._build_notify_index();bm._activate(bm._effects[0][0],NAMES[0],1.)
        self.assertEqual(self.q(bm)['capacity'],15)
        self.assertNotIn(STAT,bm.get_buffs(NAMES[0],'__enemy__',1.1))


if __name__=='__main__':unittest.main()
