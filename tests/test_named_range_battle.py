"""Full source identity, real recipient growth and stale handle exclusion."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from runner import sim
from named_range_battle import NamedRangeBattle,named_range_battle,normalize
from portable_named_range_battle_cases import fixtures,OWNER,SUPPORT
from world_actor_runtime import ActorRegistry
from impact_specs import ActorKind
class NamedRangeBattleTests(unittest.TestCase):
    def test_original_87_definitions_drive_actual_growth_and_landing(self):
        from world_named_range_battle_native import observe
        from portable_named_range_battle_contracts import verify
        case=fixtures()[0];before=copy.deepcopy(case);n,_=observe(case);result=verify(case,n)
        self.assertEqual(case,before);self.assertTrue(result['actual_battle_delivery_connected'])
        self.assertEqual((result['original_definitions'],result['max_recipients']),(87,3))
        self.assertFalse(result['gpu_supported']);self.assertEqual(result['original_support_profile'],SUPPORT)
    def test_frozen_handle_cannot_hit_a_reborn_actor_or_dead_recipient(self):
        c=fixtures()[0];runtime=NamedRangeBattle(c['named_range_rules'],c['logical_geometry']);registry=ActorRegistry();state=[1,True]
        registry.bind(ActorKind.ADD,'add',lambda:(state[0],state[1],None));handle=registry.view(ActorKind.ADD,'add').handle
        event=SimpleNamespace();runtime.pending[id(event)]=(('add',),(handle,),0);boss=object();runtime.manager=object()
        with patch('named_range_battle.registry_for',return_value=registry):
            self.assertEqual(runtime.route(boss,event,lambda *_:None),[('add',1.)])
            state[1]=False;self.assertEqual(runtime.route(boss,event,lambda *_:None),[])
            state[:]=[2,True];self.assertEqual(runtime.route(boss,event,lambda *_:None),[])
            self.assertEqual(runtime.route(boss,object(),lambda *_:'ordinary'),'ordinary')
    def test_aliases_restore_after_an_interrupted_observer_scope(self):
        case=fixtures()[0];before=(timeline.simulate,sim.simulate)
        with self.assertRaisesRegex(RuntimeError,'interrupted'):
            with named_range_battle(case['named_range_rules'],case['logical_geometry']):raise RuntimeError('interrupted')
        self.assertEqual((timeline.simulate,sim.simulate),before)
    def test_numeric_identity_and_shape_declarations_reject_ambiguous_inputs(self):
        c=fixtures()[0]
        for key,value in [('base_radius',float('nan')),('base_count',True),('base_count',129),('owner','')]:
            bad=copy.deepcopy(c['named_range_rules']);bad[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):normalize(bad,c['logical_geometry'])
        with self.assertRaises(ValueError):normalize(c['named_range_rules']*2,c['logical_geometry'])
    def test_reference_registration_does_not_imply_gpu_admission(self):
        from portable_reference import REFERENCES
        from portable_readiness_semantics import reference_readiness
        self.assertIn('named-range-battle-common',REFERENCES)
        r=reference_readiness(dict(phase='effect',kind='buff',stat='effect_range_pct',target='self'))
        self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported'])
        self.assertFalse(r['declared_named_range_battle_contract']['gpu_wire_connected'])
if __name__=='__main__':unittest.main()
