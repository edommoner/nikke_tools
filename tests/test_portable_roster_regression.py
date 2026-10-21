"""Real-input adapter retains complete effects and uses the existing oracle."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('real_regression_adapter',ROOT/'research/verify-world-roster-regression-short.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)


class RealRegressionTests(unittest.TestCase):
    def test_every_real_effect_is_prepared_without_cpu_battle_or_gpu_input(self):
        import portable_backend
        from calculator import timeline
        def forbidden(*a,**k):raise AssertionError('Execution forbidden during real static packing')
        with patch.object(timeline,'simulate',forbidden),patch.object(timeline.CharState,'tick',forbidden),patch.object(portable_backend,'execute',forbidden),patch.object(portable_backend,'build',forbidden):
            entries,data=adapter.prepare()
        self.assertEqual(len(entries),80);self.assertEqual(int.from_bytes(data[:4],'little'),80)
        self.assertEqual(len({name for name,_,_ in entries}),80)
        for _,words,(case,prepared,bound,metadata) in entries:
            from portable_specs import LIMITS as L,FIELDS as F,buff_stat_ids
            supported=buff_stat_ids()
            for row in range(words[1]):
                at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                if words[at+F['KIND']]==0:self.assertIn(words[at+F['STAT']],supported,case['character'])
            self.assertEqual(words,bound);self.assertFalse(prepared['cpu_battle_executed'])
            self.assertTrue(prepared['all_character_effects_included'])
            proof=metadata['real_prepared_input']
            self.assertTrue(proof['all_character_effects_included'])
            self.assertEqual(proof['prepared_effects'],len(prepared['effects']))
            self.assertTrue(proof['projectile_modifiers_connected'])

    def test_existing_comparator_keeps_full_native_and_shot_trace(self):
        case=dict(body=dict(public_fixture=True));prepared={};words=[1];metadata={}
        domain=(case,prepared,words,metadata);before=copy.deepcopy(domain)
        native=dict(damage=[123]);shots=[dict(time=.3)]
        with patch.object(adapter.real,'native_reference',return_value=(native,shots)),patch.object(adapter.real,'compare',return_value=(None,None,None,[])) as compare:
            self.assertEqual(adapter.compare([0],domain),dict(battle=native,skill_trace=shots))
            compare.assert_called_once_with([0],prepared,(words,metadata),native,shots)
            compare.return_value=(None,None,None,[dict(path='damage')])
            with self.assertRaisesRegex(ValueError,'difference_count'):adapter.compare([0],domain)
        self.assertEqual(domain,before)
        with self.assertRaisesRegex(ValueError,'status 64'):adapter.compare([64],domain)


if __name__=='__main__':unittest.main()
