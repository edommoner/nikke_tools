"""Declared target modifiers must preserve existing readers and final rounding."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import engine_worker
from calculator import buff_manager,damage
from destructible_damage_policy import manager_type,resolve,MODIFIERS
from destructible_modifier_cases import fixtures
from world_destructible_modifier_native import observe
from portable_destructible_modifier_contracts import verify
from test_target_counter_runtime import manager,NAMES

class ModifierPolicyTests(unittest.TestCase):
    def setup_manager(self):
        c=next(c for c in fixtures() if c['name'].endswith('/projectile'))
        seed=manager([]);cls=manager_type(type(seed));result=cls(seed.squad,state=copy.deepcopy(seed.state))
        result._effects=[(copy.deepcopy(e),NAMES[0]) for e in c['effects']];result._build_notify_index();result.notify('battle_start',0.,NAMES[0]);return result
    def query(self,bm,**changes):
        args=dict(kind=2,base_attack=1000.,weapon=engine_worker.META[NAMES[0]],defense=100.,coefficient=100.,when=.1);args.update(changes)
        return resolve(bm,NAMES[0],**args)
    def test_twenty_contracts_cover_target_axes_lifetime_and_pre_rounding(self):
        cases=fixtures();self.assertEqual(len(cases),20)
        for c in cases:
            with self.subTest(name=c['name']):n,_=observe(c);verify(c,n)
    def test_base_classes_maps_and_canonical_factor_never_change(self):
        before=(buff_manager.BuffManager.get_buffs,buff_manager.BuffManager._plan_step,dict(buff_manager._STAT_TO_BUFF),dict(buff_manager._BUFFS_ZERO),damage._factor5,damage.calc_damage)
        c=next(c for c in fixtures() if c['name'].endswith('/projectile'));observe(c)
        self.assertEqual(before,(buff_manager.BuffManager.get_buffs,buff_manager.BuffManager._plan_step,dict(buff_manager._STAT_TO_BUFF),dict(buff_manager._BUFFS_ZERO),damage._factor5,damage.calc_damage))
        plain=manager(c['effects']);plain.notify('battle_start',0.,NAMES[0]);buffs=plain.get_buffs(NAMES[0],'__enemy__',.1)
        self.assertFalse(set(MODIFIERS)&set(buffs));self.assertEqual(damage.calc_damage(1000,buffs,engine_worker.META[NAMES[0]],damage.default_hit_type(is_normal_atk=False,coeff=100),enemy_def=100,expected=True)['damage'],900)
    def test_exception_does_not_install_or_leak_a_factor(self):
        bm=self.setup_manager();before=(damage._factor5,damage.calc_damage)
        with self.assertRaises(OverflowError):self.query(bm,base_attack=1e308,coefficient=1e308)
        self.assertEqual((damage._factor5,damage.calc_damage),before)
        self.assertEqual(self.query(bm)['damage'],1350)
    def test_hit_count_shields_and_implicit_kinds_are_rejected(self):
        bm=self.setup_manager()
        for kind in (1,4,5,True,None,'2'):
            with self.subTest(kind=kind),self.assertRaises((ValueError,TypeError)):self.query(bm,kind=kind)
        with self.assertRaisesRegex(ValueError,'Explicit'):self.query(manager([]))
    def test_invalid_scalar_context_is_rejected(self):
        bm=self.setup_manager()
        for changes in [dict(base_attack=-1),dict(defense=float('nan')),dict(coefficient=True),dict(when=float('inf')),dict(full_burst=1),dict(exclude_names=['name'])]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.query(bm,**changes)
    def test_query_exclusions_use_native_owner_name_semantics(self):
        bm=self.setup_manager();self.assertEqual(self.query(bm)['damage'],1350)
        self.assertEqual(self.query(bm,exclude_names=frozenset({'projectile_dmg_pct'}))['damage'],900)
        self.assertEqual(self.query(bm)['damage'],1350)
    def test_future_native_consumers_and_unknown_query_wrappers_require_reaudit(self):
        with patch.dict(buff_manager._STAT_TO_BUFF,{'projectile_dmg_pct':'projectile_dmg_pct'}):
            with self.assertRaisesRegex(ValueError,'consumer changed'):manager_type(buff_manager.BuffManager)
        class Wrapped(buff_manager.BuffManager):
            def get_buffs(self,*args,**kwargs):return super().get_buffs(*args,**kwargs)
        with self.assertRaisesRegex(ValueError,'unwrapped'):manager_type(Wrapped)
    def test_outgoing_modifier_does_not_silently_become_an_enemy_field(self):
        c=copy.deepcopy(fixtures()[1]);c['effects'][-1]['target']='boss'
        with self.assertRaisesRegex(ValueError,'allied recipients'):observe(c)

if __name__=='__main__':unittest.main()
