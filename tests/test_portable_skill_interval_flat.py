"""Named flat periods, canonical tagged payload and independent native clocks."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_runtime import validate_effect,UnsupportedPortable
from portable_skill_interval_flat_cases import fixtures,negative_inputs
from portable_skill_interval_specs import KINDS,FLAG,MAGIC,OFFSET
from portable_specs import LIMITS as L,FIELDS as F
from world_projectile_native import observe
spec=importlib.util.spec_from_file_location('flat_interval_test',ROOT/'research/verify-world-skill-interval-flat-short.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)


class NamedIntervalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=fixtures();cls.native={c['name'].removeprefix('skill-flat-'):observe(c) for c in cls.rows}

    def clock(self,name,row=0):return next(r for r in self.native[name][0]['skill_clocks'] if r['row']==row)

    def test_both_operators_share_flat_before_percentage_and_original_floor(self):
        for value in (0,-.2,-.4,-2,.2):
            self.assertEqual(self.clock('effect_interval-'+str(value)),self.clock('skill_cooldown-'+str(value)))
        self.assertEqual(self.clock('flat-before-percent')['interval'],.1)
        self.assertEqual(self.clock('flat-positive-percent-floor')['interval'],.4*.05)
        self.assertEqual(self.clock('stacked')['interval'],.4-.1*3)

    def test_names_and_recipients_select_actual_periods(self):
        for name in ('missing-reference','empty-reference','omitted-reference','unnamed-clock-is-not-selected','other-ally'):
            self.assertEqual(self.clock(name)['interval'],.4,name)
        self.assertEqual(self.clock('other-effect-is-not-selected',0)['interval'],.2)
        self.assertEqual(self.clock('other-effect-is-not-selected',1)['interval'],.4)
        for name in ('named-ally','value-table','same-reference-unicode-colons'):
            self.assertEqual(self.clock(name)['interval'],.2,name)
        self.assertEqual(self.clock('allied-clocks',1)['interval'],.2)

    def test_runtime_gates_and_lifecycle_keep_native_clock_rescaling(self):
        self.assertEqual(self.clock('runtime-false')['interval'],.4)
        self.assertEqual(self.clock('runtime-ally-hp-context')['interval'],.4)
        self.assertEqual(self.clock('runtime-ally-hp-matches-query-caster')['interval'],.2)
        self.assertEqual(self.clock('runtime-crosses')['interval'],.2)
        self.assertNotEqual(self.clock('expire-mid-period')['due'],self.clock('effect_interval-0')['due'])
        self.assertEqual(self.clock('expire-mid-period')['interval'],.4)
        self.assertGreater(len(self.native['finite-keeps-activation-gate'][1]),3)

    def test_stat_order_and_existing_sum_avoid_false_overflow_or_lost_small_term(self):
        self.assertEqual(self.clock('two-stats-overflow-order')['interval'],1e308)
        self.assertEqual(self.clock('compensated-small-amount')['interval'],.2)
        self.assertEqual(self.clock('two-stats-sum-order')['interval'],.5)
        self.assertEqual(self.clock('with-trigger-reducer')['interval'],.2)
        self.assertEqual(self.clock('with-stack-operation')['interval'],.4-.1*3)

    def test_private_canonical_kind_and_union_are_static_and_immutable(self):
        for c in self.rows:
            before=copy.deepcopy(c);words,_,_=adapter.suite.compile_case(c)
            for row,effect in enumerate(c['effects']):
                if effect.get('stat') not in KINDS:continue
                for options in ({},dict(combat={}),dict(world_frame=True)):
                    with self.assertRaises(UnsupportedPortable):validate_effect(effect,**options)
                validate_effect(effect,combat={},world_frame=True)
                d=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];meta=L['MODE_BASE']+row*L['MODE_WORDS']+OFFSET
                self.assertEqual(words[d+F['KIND']],4);self.assertEqual(words[d+F['STAT']],0)
                self.assertEqual(words[meta:meta+2],[MAGIC,KINDS[effect['stat']]])
                self.assertEqual(words[meta+3],int(bool(effect.get('target_effect'))))
                self.assertEqual(words[L['DEFINITION_EXTRA_BASE']+row*L['DEFINITION_EXTRA_WORDS']+3],FLAG)
            self.assertEqual(c,before)
        self.assertEqual(len(negative_inputs(adapter.suite.compile_case)),17)
        for invalid in (None,1,[]):
            c=copy.deepcopy(self.rows[0]['effects'][1]);c['target_effect']=invalid
            with self.assertRaises(UnsupportedPortable):validate_effect(c,combat={},world_frame=True)


if __name__=='__main__':unittest.main()
