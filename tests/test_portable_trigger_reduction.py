"""Native counter semantics and static canonical bindings, without GPU replay."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('reduction_adapter',ROOT/'research/verify-world-trigger-reduction-short.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
from portable_trigger_reduction_cases import fixtures,negative_inputs
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L,check_schema


class TriggerReductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=fixtures();cls.by_name={c['name'].removeprefix('trigger-reduction-'):c for c in cls.rows}
        cls.native={name:adapter.suite.inspect_native(c) for name,c in cls.by_name.items()}

    def times(self,name):
        case=self.by_name[name];row=next(i for i,e in enumerate(case['effects']) if e['name']=='proc')
        return [e['created'] for e in self.native[name][1] if e['row']==row]

    def test_sum_is_truncated_once_and_threshold_is_at_least_one(self):
        self.assertEqual(self.times('sum-before-positive-truncate'),self.times('value-1'))
        self.assertEqual(self.times('sum-before-negative-truncate'),self.times('value--1'))
        self.assertEqual(self.times('value-0.75'),self.times('baseline'))
        self.assertEqual(self.times('value--0.75'),self.times('baseline'))
        self.assertGreater(len(self.times('value-100')),len(self.times('value-1')))
        self.assertEqual(self.times('threshold-above-counter-horizon'),[])

    def test_caster_raw_timing_and_fixed_literal_contract(self):
        for name in ('empty-target-name','absent-target-name','other-caster','raw-placeholder-timing-is-not-intersection','missing-fixed-value-ignores-level-values'):
            self.assertEqual(self.times(name),self.times('baseline'),name)
        for name in ('other-recipient-still-caster-bound','stack-is-not-a-multiplier','shared-timing-group','runtime-predicate-changes-after-activation'):
            self.assertEqual(self.times(name),self.times('value-1'),name)

    def test_expiry_activation_guard_and_nonreducible_stage_boundaries(self):
        self.assertEqual(self.times('finite-expiry'),self.times('baseline'))
        self.assertEqual(self.times('finite-false-condition-does-not-activate'),self.times('baseline'))
        self.assertEqual(self.times('refresh-before-expiry'),self.times('value-1'))
        self.assertEqual(self.times('same-name-refresh-latest-definition'),self.times('value-1'))
        self.assertEqual(self.times('not-reducible-burst_enter_count:1:2'),[])
        self.assertGreater(len(self.times('not-reducible-received_hit_count:2')),0)
        self.assertGreater(len(self.times('counter-core_hit_count:4')),0)

    def test_static_mask_reuses_canonical_owner_and_raw_timing_identity(self):
        for name,expected in [('shared-timing-group',6),('raw-placeholder-timing-is-not-intersection',2),('other-caster',0)]:
            c=self.by_name[name];before=copy.deepcopy(c);words,_,_=adapter.suite.compile_case(c)
            self.assertEqual(words[L['MODE_BASE']+L['TRIGGER_REDUCTION_OFFSET']],L['TRIGGER_REDUCTION_MAGIC'])
            self.assertEqual(words[L['MODE_BASE']+L['TRIGGER_REDUCTION_MASK']],expected)
            self.assertEqual(c,before)
        check_schema();self.assertEqual(len(negative_inputs(adapter.suite.compile_case)),8)

    def test_private_boundary_and_malformed_definitions_fail_before_execution(self):
        effect=self.by_name['value-1']['effects'][0]
        for options in ({},dict(combat={})):
            with self.assertRaises(UnsupportedPortable):validate_effect(effect,**options)
        validate_effect(effect,combat={},world_frame=True)
        for change in (dict(type='instant'),dict(fixed_value=True),dict(fixed_value=float('nan')),dict(fixed_value=1e9),dict(fixed_value=1<<2048),dict(target_effect=[])):
            with self.assertRaises(UnsupportedPortable):validate_effect(dict(effect,**change),combat={},world_frame=True)

    def test_charge_fixtures_match_native_static_clock_normalization(self):
        from calculator import timeline
        from world_frame_native import authored_metadata,roster_names
        for case in self.rows:
            if not any(w.get('mode')=='charge' for w in case['combat']['weapons']):continue
            metadata=authored_metadata(case);names=roster_names(case)
            with patch.dict(timeline._NIKKE,metadata),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True):
                for i,(name,weapon) in enumerate(zip(names,case['combat']['weapons'])):
                    if weapon.get('mode')!='charge':continue
                    actor=timeline.CharState(dict(name=name,skill_levels={'1':10,'2':10,'3':10}),case['base_atk'][i],None)
                    self.assertEqual(weapon['min_cycle'],actor._min_fire_cycle)
                    self.assertEqual(case['post_fire_delays'][i],actor.post_fire_delay)
                    self.assertEqual(weapon['charge'],actor.charge_time_base)


if __name__=='__main__':unittest.main()
