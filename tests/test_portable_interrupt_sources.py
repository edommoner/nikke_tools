import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('app','research')]
import engine_worker
from calculator.boss_pattern import validate,BossScript
from impact_specs import ActorKind,ActorHandle
from portable_actor_specs import compile_registry
from portable_actor_pool_specs import compile_pools
from portable_interrupt_specs import KIND,SOURCE,pool_bindings,InterruptBinding
from world_actor_specs import bindings
from world_actor_pool_native import pool_rows
class InterruptSourcesTests(unittest.TestCase):
    def test_full_native_observer_never_queries_private_numeric_targets(self):
        from calculator.buff_manager import BuffManager
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('interrupt_observer',root/'research/verify-world-parts-skill-short.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        case=next(c for c in adapter.fixtures() if c['name']=='parts-skill-interrupt-only')
        original=BuffManager.get_buffs
        original_flat=BuffManager.enemy_atk_down_flat
        def guarded(manager,*args,**kwargs):
            target=args[1] if len(args)>1 else kwargs.get('target')
            if isinstance(target,str) and target.startswith('stop'):raise AssertionError('Private target numeric query')
            return original(manager,*args,**kwargs)
        def guarded_flat(manager,target,*args,**kwargs):
            if isinstance(target,str) and target.startswith('stop'):raise AssertionError('Private target attack query')
            return original_flat(manager,target,*args,**kwargs)
        with patch.object(BuffManager,'get_buffs',guarded),patch.object(BuffManager,'enemy_atk_down_flat',guarded_flat):native,_=adapter.observe(case)
        self.assertEqual(native['enemy_fields']['queries'][-1],[1]+[0]*11)
        self.assertEqual(native['enemy_attack_fields'][-1]['flat'],0)
    def patterns(self,count=1):return validate([dict(id='stop',kind='interrupt',targets=[dict(name='stop-'+str(i),hp=100,reach=1) for i in range(count)])])
    def test_private_identity_never_reuses_projectile_or_canonical_impact(self):
        self.assertEqual(int(ActorKind.PROJECTILE),2);self.assertEqual((KIND,SOURCE),(6,3))
        with self.assertRaises(ValueError):ActorHandle(KIND,0)
        p=self.patterns();self.assertEqual(len(bindings(p)),1)
        rows=pool_bindings(p);self.assertIsInstance(rows[1],InterruptBinding);self.assertIsNone(rows[1].parent)
    def test_literal_tables_without_native_lifecycle_or_hp_queries(self):
        p=self.patterns()
        with patch.object(BossScript,'begin_frame',side_effect=AssertionError('Not input')),patch.object(BossScript,'hit_target',side_effect=AssertionError('Not input')):
            w,rows=compile_registry(p,pools=True);q=compile_pools(p,rows)
        self.assertEqual(w[8:10],[3,1]);self.assertEqual(w[8+128+8:8+128+16],[6,0,3,0,0,0xffffffff,0xffffffff,0])
        self.assertEqual(q[20:24],[1,0,0,1079574528]) # literal100 binary64
        with self.assertRaises(ValueError):compile_registry(p)
    def test_capacity_precedes_private_binding_expansion(self):
        with patch('portable_interrupt_specs.pool_bindings',side_effect=AssertionError('No allocation')),self.assertRaisesRegex(ValueError,'capacity'):compile_registry(self.patterns(128),pools=True)
        _,rows=compile_registry(self.patterns(127),pools=True);self.assertEqual(len(rows),128)
    def test_native_generation_and_expiry_are_observed_from_actual_run(self):
        p=validate([dict(id='stop',kind='interrupt',delay=.05,until={'time':.05},targets=[dict(name='stop',hp=100,reach=1)],after=['start','stop'],repeat=2)])
        enemy={'def':0,'core_px':0};boss=BossScript(p,enemy,lambda *_:False)
        self.assertEqual(pool_rows(boss)[1],[0]*16)
        for i in range(16):boss.begin_frame(i/60,enemy)
        row=pool_rows(boss)[1];self.assertEqual(row[:4],[2,0,0,0]);self.assertEqual(row[4:8],[0]*4)
