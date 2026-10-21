"""Real preparation integrity and fail-closed world policy boundaries."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from detail_coverage import body_for
from portable_specs import LIMITS as L,FIELDS as F
from portable_world_roster_input import compile_world_battle
from portable_runtime import UnsupportedPortable
from calculator import timeline
import portable_backend
NAMES=['미란다','도라','N102','메어리','드레이크']

def prepared():
    return engine_worker.evaluate(dict(body_for(NAMES,3,grown=True),burst_gauge_mode='accumulate',_portable_static_inputs=True))

class RealWorldInputTests(unittest.TestCase):
    def test_all_definitions_and_original_input_preserved_without_battle(self):
        p=prepared();before=copy.deepcopy(p)
        with patch.object(timeline.CharState,'tick',side_effect=AssertionError('No CPU ticks')),patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle')),patch.object(portable_backend,'execute',side_effect=AssertionError('No GPU')),patch.object(portable_backend,'build',side_effect=AssertionError('No build')):
            w,m=compile_world_battle(p)
        self.assertEqual(p,before)
        self.assertEqual((len(w),w[0],w[L['TARGET_COUNTER_INPUT_BASE']+6]),(104400,0x5045568c,23))
        self.assertEqual(m['binding_source_indices'],list(range(len(p['effects']))))
        self.assertEqual(m['effects'],[e['effect']['name'] for e in p['effects']])
        self.assertTrue(m['real_prepared_input']['all_character_effects_included'])
        self.assertFalse(m['real_prepared_input']['cpu_battle_executed'])
        self.assertFalse(m['real_prepared_input']['full_catalog_certified'])
        self.assertEqual([w[L['COMMAND_BASE']+8*i] for i in range(w[2])],[24,30,2,40])

    def test_actual_growth_and_skill_levels_reach_quantity_compiler(self):
        p=prepared();w,_=compile_world_battle(p)
        p2=engine_worker.evaluate(dict(body_for(NAMES,3,grown=False),burst_gauge_mode='accumulate',_portable_static_inputs=True))
        w2,_=compile_world_battle(p2)
        self.assertNotEqual(p['base_atk'],p2['base_atk'])
        self.assertNotEqual(w,w2)
        self.assertEqual(w[1],len(p['effects']))

    def test_enemy_descriptors_and_actor_pools_not_cpu_lifetimes(self):
        p=prepared();p['enemy']['patterns']=[dict(id='wave',kind='summon',spec=dict(count=2,hp=100))]
        w,m=compile_world_battle(p)
        self.assertEqual(m['real_prepared_input']['actor_bindings'],3)
        self.assertEqual(w[L['WORLD_ACTOR_INPUT_BASE']+1],3)

    def test_unsupported_effect_never_filtered(self):
        p=prepared();p['effects'].append(dict(owner=NAMES[0],effect=dict(name='unconnected',type='instant',stat='revive',fixed_value=50,target='all_allies',trigger=dict(timing=['battle_start'],condition=[]))))
        with self.assertRaises(ValueError):compile_world_battle(p)

    def test_unmodeled_policy_rejected(self):
        for field,value in [('burst_gauge_mode','time'),('aim_interrupt',True),('unknown',1)]:
            p=prepared();p['policies']['config'][field]=value
            with self.subTest(field=field),self.assertRaises(UnsupportedPortable):compile_world_battle(p)
        p=prepared();p['policies']['auto'].remove(NAMES[0])
        with self.assertRaises(UnsupportedPortable):compile_world_battle(p)

    def test_controls_cannot_disappear_between_preparation_and_packing(self):
        p=prepared();p['policies']['controls'][NAMES[0]]={'click':[{'mode':'tap'}]}
        with self.assertRaises(UnsupportedPortable):compile_world_battle(p)
        p=prepared();p['chars'][0]['control']={'reload':[0.2]};p['policies']['controls'][NAMES[0]]=copy.deepcopy(p['chars'][0]['control'])
        with self.assertRaises(ValueError):compile_world_battle(p)

if __name__=='__main__':unittest.main()
