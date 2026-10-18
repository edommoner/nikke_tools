"""One predicate contract for every character, independent of battle fixtures."""
import unittest
from world_condition_specs import count_condition,gpu_source_matches,specialize_static_counts


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
        self.assertTrue(gpu_source_matches())
        for text,want in [('enemy_count_above:3',(40,3)),('enemy_count_below:2',(41,2)),('enemy_count_above:-1',(40,-1)),('enemy_count_below:+0',(41,0))]:
            with self.subTest(text=text):self.assertEqual(count_condition(text),want)
        for text in ('enemy_count_above:1.5','enemy_count_below:nan','enemy_count_above:','enemy_count_above:2147483648','enemy_count_below:2:3','target_is_add'):
            with self.subTest(text=text),self.assertRaises(ValueError):count_condition(text)

    def test_forged_count_descriptors_are_rejected_before_cuda(self):
        import copy
        from detail_coverage import a
        from test_target_counter_runtime import NAMES,manager
        from detail_gpu import compile_effects,run
        effect=dict(name='count',source='스킬1',type='buff',stat='atk_pct',fixed_value=17,target='self',duration=-1,trigger=dict(timing=['passive'],condition=['enemy_count_above:3']))
        bm=manager([effect]);chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES]
        program=compile_effects(chars,bm._effects)
        for field,value in ((14,4),(16,1),(17,.5),(17,2147483648),(15,40.5),(15,42)):
            bad=copy.deepcopy(program);bad['effects'][0][field]=value
            with self.subTest(field=field,value=value),self.assertRaisesRegex(ValueError,'condition descriptor'):
                run(None,[bad],[[0,2,0,0,0,0,0,0]],[[0,0]],[bm.state['base_stats']])
