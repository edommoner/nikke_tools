"""One predicate contract for every character, independent of battle fixtures."""
import unittest
from world_condition_specs import count_condition,specialize_static_counts


class WorldConditionTests(unittest.TestCase):
    def test_static_specialization_never_uses_current_living_population(self):
        import copy
        row=[0]*344;row[14]=3;row[15:24]=[40,0,3,41,0,2,22,0,1]
        dynamic=copy.deepcopy(row)
        self.assertEqual(specialize_static_counts([dynamic],has_add_sources=True),0)
        self.assertEqual(dynamic,row)
        static=copy.deepcopy(row)
        self.assertEqual(specialize_static_counts([static],has_add_sources=False),2)
        self.assertEqual(static[15:24],[22,0,0,22,0,1,22,0,1])
        self.assertEqual(specialize_static_counts([static],has_add_sources=False),0)
        for flag in (None,0,1):
            with self.subTest(flag=flag),self.assertRaises(ValueError):specialize_static_counts([row],has_add_sources=flag)

    def test_integer_thresholds_and_generated_gpu_contract(self):
        for text,want in [('enemy_count_above:3',(40,3)),('enemy_count_below:2',(41,2)),('enemy_count_above:-1',(40,-1)),('enemy_count_below:+0',(41,0))]:
            with self.subTest(text=text):self.assertEqual(count_condition(text),want)
        for text in ('enemy_count_above:1.5','enemy_count_below:nan','enemy_count_above:','enemy_count_above:2147483648','enemy_count_below:2:3','target_is_add'):
            with self.subTest(text=text),self.assertRaises(ValueError):count_condition(text)
