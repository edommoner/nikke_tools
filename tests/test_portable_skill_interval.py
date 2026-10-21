"""Persistent percentages: native clock state, guards and unchanged source data."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_runtime import validate_effect,UnsupportedPortable
from portable_skill_interval_cases import fixtures,negative_inputs
from portable_specs import LIMITS as L,FIELDS as F
from world_projectile_native import observe
spec=importlib.util.spec_from_file_location('interval_adapter_test',ROOT/'research/verify-world-skill-interval-short.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)


class SkillIntervalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=fixtures();cls.native={c['name'].removeprefix('skill-interval-'):observe(c) for c in cls.rows}

    def clock(self,name,row=0):
        return next(r for r in self.native[name][0]['skill_clocks'] if r['row']==row)

    def test_floor_uses_ordered_binary64_and_not_rounded_percent(self):
        self.assertEqual(self.clock('percent-0')['interval'],.4)
        self.assertEqual(self.clock('percent--50')['interval'],.2)
        self.assertEqual(self.clock('percent--100')['interval'],.4*.05)
        self.assertEqual(self.clock('percent--100'),self.clock('percent--200'))
        # -95% is a different rounding path from the literal5% cap.
        self.assertGreater(self.clock('percent--95')['interval'],self.clock('percent--100')['interval'])
        self.assertLess(len(self.native['percent-50'][1]),len(self.native['percent-0'][1]))
        self.assertEqual(self.clock('compensated-cancellation'),self.clock('percent--50'))
        self.assertEqual(self.native['positive-sum-overflow'][1],[])
        self.assertEqual(self.clock('positive-sum-overflow')['due'],float('inf'))

    def test_remainder_rescales_on_activation_expiry_and_with_instant_reduction(self):
        for name in ('activate-mid-period','expire-mid-period','activate-and-expire'):
            self.assertNotEqual(self.clock(name)['due'],self.clock('percent-0')['due'])
        self.assertEqual(self.clock('expire-mid-period')['interval'],.4)
        self.assertEqual(self.clock('interacts-with-one-shot-remainder')['interval'],.2)
        self.assertNotEqual(self.clock('interacts-with-one-shot-remainder')['due'],self.clock('percent--50')['due'])

    def test_native_container_semantics_ignore_runtime_predicate_and_target_effect_filter(self):
        for name in ('passive-runtime-false-is-not-rechecked','runtime-crossing-does-not-gate-percent',
                     'target-effect-is-not-percent-filter','level-values','overlapping-target-set'):
            self.assertEqual(self.clock(name),self.clock('percent--50'),name)
        self.assertEqual(self.clock('finite-activation-condition-false'),self.clock('percent-0'))
        self.assertEqual(self.clock('excluded-clock'),self.clock('percent-0'))
        self.assertEqual(self.clock('named-ally'),self.clock('percent--50'))
        self.assertEqual(self.clock('down-clock-keeps-advancing')['interval'],.4)

    def test_canonical_stat_private_admission_and_input_immutability(self):
        for c in self.rows:
            before=copy.deepcopy(c);words,_,_=adapter.suite.compile_case(c)
            for row,effect in enumerate(c['effects']):
                if effect.get('stat')!='skill_cooldown_pct':continue
                for options in ({},dict(combat={}),dict(world_frame=True)):
                    with self.assertRaises(UnsupportedPortable):validate_effect(effect,**options)
                validate_effect(effect,combat={},world_frame=True)
                self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['STAT']],58)
                self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['KIND']],0)
            self.assertEqual(c,before)
        self.assertEqual(len(negative_inputs(adapter.suite.compile_case)),4)


if __name__=='__main__':unittest.main()
