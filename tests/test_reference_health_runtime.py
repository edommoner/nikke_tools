import ast
import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import engine_worker
from calculator.buff_manager import BuffManager
from damage_query_runtime import DamageQueryScope


class ReferenceHealthIndexTests(unittest.TestCase):
    def manager(self):
        manager=BuffManager.__new__(BuffManager)
        manager.state={'base_stats':{'a':{'hp':1023.123},'b':{'hp':912.345}}}
        manager._active=[];manager._stat_index={};manager._cache_version=0
        manager._buffs_cache={};manager._stunned_cache={};manager._plan_cache={};manager._name_index_cache={}
        manager._get_value=lambda effect,ab,name:effect['value']*ab.stack
        manager._runtime_condition_ok=lambda *args:False
        manager._cur_t=0
        return manager

    def carrier(self,stat,value=0.123,name='ordinary',**fields):
        return NS(effect={'stat':stat,'value':value,'name':name},caster='b',target_chars=['a'],
                  hp_bonus_flat=value,copy_basis=912.345,has_runtime_conditions=False,stack=1,**fields)

    def exact(self,manager,scope=None):
        actual=manager.effective_max_hp('a',query_scope=scope)
        expected=BuffManager.effective_max_hp.__wrapped__(manager,'a',query_scope=scope)
        self.assertEqual(actual,expected)
        return actual

    def test_multiple_stats_interleaved_and_copy_preserve_float_order(self):
        stats=['max_hp_pct','hp_caster_based_pct','max_hp_only_pct','hp_only_caster_based_pct','max_hp_from_max_hp_pct']
        for count in (2,3,5):
            for copied in (False,True):
                with self.subTest(count=count,copied=copied):
                    m=self.manager()
                    for repeat,value in enumerate((1e16,0.123,-1e16,9.876)):
                        for stat in stats[:count]+(['hp_copy'] if copied else []):
                            m._active.extend([self.carrier('atk_pct'),self.carrier(stat,value)])
                    self.exact(m)
                    cached=next(iter(m._stat_index.values()))
                    self.assertEqual([id(ab) for ab in cached],[id(ab) for ab in m._active if ab.effect['stat']!='atk_pct'])
                    self.exact(m,DamageQueryScope('b',{'ordinary'}))
                    m._active[1].stack=2 # values are deliberately never cached
                    self.exact(m)

    def test_targets_conditions_and_builtin_query_scope(self):
        m=self.manager()
        for stat in ('max_hp_pct','hp_copy','max_hp_from_max_hp_pct'):
            ab=self.carrier(stat);ab.has_runtime_conditions=True
            ab.effect['trigger']={'condition':['during_shield']};m._active.append(ab)
        self.exact(m)
        m._active[0].target_chars=None
        self.exact(m,DamageQueryScope('b',{'ordinary'}))
        self.exact(m,DamageQueryScope('a',{'ordinary'}))

    def test_minimal_manager_and_observable_custom_scope_fall_back(self):
        m=self.manager();m._active=[self.carrier('atk_pct'),self.carrier('hp_copy')]
        seen=[]
        scope=NS(excludes=lambda ab:seen.append(ab) or False)
        m.effective_max_hp('a',query_scope=scope)
        fast_seen=list(seen);seen.clear()
        BuffManager.effective_max_hp.__wrapped__(m,'a',query_scope=scope)
        self.assertEqual(seen,fast_seen)
        minimal=NS(state=m.state,_active=[],_get_value=m._get_value)
        self.assertEqual(BuffManager.effective_max_hp(minimal,'a'),1023.123)

    def test_real_activation_expiry_removal_and_reset_invalidate(self):
        # Use the real lifecycle, not synthetic mutation/invalidation pairs.
        import importlib.util
        path=Path(__file__).resolve().parents[1]/'scripts/verify-base-copy.py'
        spec=importlib.util.spec_from_file_location('health_index_helpers',path)
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        effect=helper.B('HP index witness','max_hp_pct',17,event='on_attack',duration=.5)
        class Manager(BuffManager):
            def _register_all(self):
                self._effects=[(effect,helper.N[0])];self._build_notify_index()
        bs={n:dict(atk=1000,**{'def':0},hp=1000) for n in helper.N}
        m=Manager(helper.v.characters(helper.N),state=dict(base_stats=bs,hp={n:1000 for n in helper.N},hp_pct={n:100 for n in helper.N},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={},rng_expected=True,camera=set()))
        def check():
            self.assertEqual(m.effective_max_hp(helper.N[0]),BuffManager.effective_max_hp.__wrapped__(m,helper.N[0]))
        check();m.notify('on_attack',.1,helper.N[0]);check()
        self.assertTrue(m._active)
        m.tick(1);check();self.assertFalse(m._active)
        m.notify('on_attack',1.1,helper.N[0]);check()
        remove=helper.E('remove witness','instant','remove_named_buff',0,target_effect='HP index witness')
        m._dispatch_instant(remove,helper.N[0],1.2);check();self.assertFalse(m._active)
        m.notify('on_attack',1.3,helper.N[0]);check();m.reset();check();self.assertFalse(m._active)

    def test_unexpected_loop_shape_fails_at_install(self):
        import reference_health_runtime as runtime
        original=BuffManager.effective_max_hp.__wrapped__
        for changed in ('prelude','default','nested'):
            def replacement(*args,**kwargs):return original(*args,**kwargs)
            replacement._nikke_reference_tree=copy.deepcopy(original._nikke_reference_tree)
            loop=next(n for n in ast.walk(replacement._nikke_reference_tree) if isinstance(n,ast.For))
            if changed=='prelude':loop.body.insert(0,ast.parse('self.observe(ab)').body[0])
            elif changed=='default':
                branch=loop.body[-1]
                while branch.orelse:branch=branch.orelse[0]
                branch.orelse=ast.parse('self.observe(ab)').body
            else:loop.body[-1].body.append(ast.parse('if stat == "hidden": self.observe(ab)').body[0])
            with self.subTest(changed=changed),patch.object(BuffManager,'_nikke_reference_health',False),patch.object(BuffManager,'effective_max_hp',replacement):
                with self.assertRaises(AssertionError):runtime.install()

    def test_index_clear_and_replacement_discard_cached_iterable(self):
        m=self.manager();self.exact(m)
        for invalidate in (m._invalidate_buffs_cache,lambda:setattr(m,'_stat_index',{})):
            m._active.append(self.carrier('hp_copy'));invalidate();self.exact(m)


if __name__=='__main__':unittest.main()
