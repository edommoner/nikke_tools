"""Read actual native outcomes; packing must not supply simulated hit context."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('skill_critical_adapter',ROOT/'research/verify-world-skill-critical-short.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
from portable_skill_critical_cases import fixtures,negative_inputs
from portable_specs import LIMITS as L,FIELDS as F,check_schema
from portable_runtime import validate_effect,UnsupportedPortable


class SkillCriticalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=fixtures();cls.cases={c['name'].removeprefix('skill-critical-'):c for c in cls.rows}
        cls.native={k:adapter.suite.inspect_native(c) for k,c in cls.cases.items()}

    def trace(self,name,effect='witness'):
        c=self.cases[name];ids={i for i,e in enumerate(c['effects']) if e['name']==effect}
        return [r for r in self.native[name][1] if r['row'] in ids]

    def test_fractional_unit_and_zero_use_actual_per_name_accumulators(self):
        self.assertEqual(self.trace('rate--100'),[])
        self.assertGreater(len(self.trace('rate-35')),len(self.trace('rate-0')))
        self.assertEqual(len(self.trace('rate-85')),len(self.trace('rate-200')))
        self.assertEqual(self.native['rate-85'][0]['skill_critical'],[])
        self.assertTrue(self.native['rate-35'][0]['skill_critical'])
        self.assertEqual(self.native['rate--100'][0]['rng'],self.native['rate-200'][0]['rng'])

    def test_nested_children_restore_parent_but_fresh_notify_has_no_context(self):
        n='siblings-restore-parent-context'
        self.assertEqual(len(self.trace(n)),len(self.trace(n,'second-witness')))
        self.assertLess(len(self.trace(n,'nested')),len(self.trace(n)))
        n='empty-notify-does-not-inherit-critical-parent'
        self.assertEqual(self.trace(n,'leak'),[])
        self.assertGreater(len(self.trace(n,'positive-notice')),0)
        for name in self.cases:
            if name.startswith('no-context-'):self.assertEqual(self.trace(name),[],name)

    def test_snapshots_normal_formulas_and_deferred_burst_keep_distinct_paths(self):
        self.assertEqual(len([r for r in self.trace('multi-hit-snapshot-before-critical-child') if r['created']==0]),1)
        self.assertEqual(len(self.trace('normal-only-rate-does-not-boost-skill')),len(self.trace('rate-0')))
        self.assertGreater(len(self.trace('normal-formula-uses-normal-rate')),len(self.trace('rate-0')))
        for name in ('zero-coefficient-emits-no-context','unnamed-packet-emits-no-context','deferred-burst-emits-no-named-hit'):
            self.assertEqual(self.trace(name),[])
            self.assertEqual(self.native[name][0]['skill_critical'],[])

    def test_canonical_condition_and_named_marker_are_static_and_private(self):
        for case in self.rows:
            before=copy.deepcopy(case);words,_,_=adapter.suite.compile_case(case)
            self.assertEqual(words[L['WORLD_META_BASE']+3],1)
            self.assertEqual(case,before)
        effect=self.rows[0]['effects'][-1]
        with self.assertRaises(UnsupportedPortable):validate_effect(effect,combat={},world_frame=False)
        validate_effect(effect,combat={},world_frame=True)
        words,_,_=adapter.suite.compile_case(self.rows[2])
        self.assertEqual(words[L['CONDITION_BASE']+2*L['CONDITION_WORDS']],28)
        self.assertEqual(len(negative_inputs(adapter.suite.compile_case)),10);check_schema()
        from portable_projectile_specs import TRACE,TRACE_COUNT
        self.assertGreaterEqual(L['SKILL_CRITICAL_STATE_BASE'],TRACE+16*TRACE_COUNT)
        self.assertLessEqual(L['SKILL_CRITICAL_STATE_BASE']+L['SKILL_CRITICAL_STATE_WORDS'],786416)

    def test_forced_slots_check_conditions_without_resetting_periods(self):
        self.assertEqual(self.trace('forced-slot-checks-condition','forced'),[])
        self.assertGreater(len(self.trace('forced-slot-preserves-hit-context','forced')),0)
        self.assertEqual(len(self.trace('forced-slot-starts-inactive-rate')),len(self.trace('rate-85')))
        times=[r['created'] for r in self.trace('forced-slot-preserves-period-grid','source')]
        baseline=copy.deepcopy(self.cases['forced-slot-preserves-period-grid'])
        baseline['effects']=baseline['effects'][:2];baseline['owners']=baseline['owners'][:2]
        _,trace=adapter.suite.inspect_native(baseline)
        clock_times=[r['created'] for r in trace if r['row']==0]
        self.assertTrue(clock_times)
        self.assertTrue(all(t in times for t in clock_times))
        self.assertGreater(len(times),len(clock_times))
        self.assertTrue(any(.3<=t<.4 for t in times))


if __name__=='__main__':unittest.main()
