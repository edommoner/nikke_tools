import copy
import math
import importlib.util
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'scripts', 'tests', 'research')]
import portable_target_counter_specs as wire
from impact_specs import ActorHandle, Impact, impact_command, decode_command
from portable_runtime import validate_effect, UnsupportedPortable
from portable_trigger_specs import validate_input
from target_counter_cases import clone_cases, marker
from test_target_counter_runtime import NAMES
from world_target_counter_native import activation_child_witness


class CounterInputContracts(unittest.TestCase):
    def test_all_shared_stimuli_have_lossless_canonical_impact_encoding(self):
        for case in clone_cases():
            symbols = {e['name']: i for i, e in enumerate(case['effects'])}
            words = wire.pack([(e, 0) for e in case['effects']], case['actions'], NAMES, symbols)
            self.assertEqual(len(words), wire.INPUT_WORDS)
            for i, (time, action) in enumerate(case['actions']):
                at = wire.ACTION_BASE + i * wire.ACTION_WORDS
                row = words[at:at + wire.ACTION_WORDS]
                self.assertEqual(struct.unpack('<d', struct.pack('<II', *row[1:3]))[0], time)
                if action[0] == 'hit':
                    f, o, k, identity, gen, credit, damage, *who = action[1:]
                    original = Impact(NAMES[who[0] if who else 2], ActorHandle(k, identity, gen), f, o, damage, credit)
                    decoded = Impact(NAMES[row[3]], ActorHandle(*row[4:7]), row[7], row[8],
                                     struct.unpack('<d', struct.pack('<II', *row[9:11]))[0],
                                     struct.unpack('<d', struct.pack('<II', *row[11:13]))[0], row[13])
                    self.assertEqual(decoded, decode_command(impact_command(time, original, NAMES), NAMES))
            # Expected CPU output is not an encoder argument or input field.
            changed = copy.deepcopy(case); changed['expected'] = ['poison']
            self.assertEqual(words, wire.pack([(e, 0) for e in changed['effects']], changed['actions'], NAMES, symbols))

    def test_exact_unknown_actor_and_fractional_credit_are_not_body_or_damage(self):
        e = marker(threshold=1e12, actor=dict(kind='add', identity=2**28-1, generation=2**31-1))
        words = wire.pack([(e, 4)], [(0, ('activate',)), (0, ('hit', 3, 1, 5, 2**28-1, 2**31-1, .75, 0, 4))], NAMES, {'marker': 255})
        self.assertEqual(words[wire.POLICY_BASE:wire.POLICY_BASE+4], [1, 5, 2**28-1, 2**31-1])
        at = wire.ACTION_BASE + wire.ACTION_WORDS
        self.assertEqual(words[at+4:at+7], [5, 2**28-1, 2**31-1])
        self.assertEqual(words[at+9:at+13], [0, 0, 0, 0x3fe80000])

    def test_named_policy_conflicts_and_all_stack_operations_fail_closed(self):
        first = marker(); second = marker(threshold=3)
        with self.assertRaisesRegex(ValueError, 'identical'):
            wire.pack([(first, 0), (second, 0)], [(0, ('activate',))], NAMES, {'marker': 0})
        wire.pack([(first, 0), (second, 1)], [(0, ('activate',))], NAMES, {'marker': 0})
        for stat in ('buff_stack_add', 'buff_stack_remove', 'buff_stack_init', 'buff_max_stack_add', 'debuff_stack_add', 'debuff_stack_remove'):
            with self.subTest(stat=stat), self.assertRaisesRegex(ValueError, 'separate'):
                wire.pack([(first, 0), (dict(stat=stat, target_effect='marker'), 0)], [(0, ('activate',))], NAMES, {'marker': 0})

    def test_invalid_literal_time_quantity_enum_and_capacity_rejected_before_gpu(self):
        for time, action in [(math.nan, ('activate',)), (-1, ('activate',)), (181, ('activate',)),
                             (0, ('hit', 0, 0, 0, 0, 1, 1, 0)),
                             (0, ('hit', 0, 1, 0, 0, 1, 1, 1)),
                             (0, ('hit', 0, 2, 0, 0, 1, math.inf, 1)),
                             (0, ('hit', 0, 2, 6, 0, 1, 1, 1)),
                             (0, ('hit', 0, 2, 0, 0, 1, 1, 1, True)),
                             (0, ('death', 0, 0, 0)), (0, ('unknown',))]:
            with self.subTest(action=action, time=time), self.assertRaises(ValueError):
                wire.action_words(time, action, NAMES)
        for effects, actions in [([(marker(), 0)] * 257, [(0, ('activate',))]),
                                 ([(marker(), 0)], [(0, ('activate',))] * 65),
                                 ([(marker(), 0)], [(1, ('activate',)), (0, ('refresh',))])]:
            with self.assertRaises(ValueError): wire.pack(effects, actions, NAMES, {'marker': 0})

    def test_public_gpu_admission_remains_closed(self):
        with self.assertRaises(UnsupportedPortable): validate_effect(marker(), world_frame=True)
        e = marker(); e['trigger']['timing'] = ['event:target_counter_complete:marker']
        with self.assertRaises(ValueError): validate_input(e, world_frame=True)

    def test_resource_is_ready_before_named_activation_children(self):
        witness = activation_child_witness()
        self.assertTrue(witness['preparation_precedes_named_activation_children'])
        self.assertEqual(witness['final_live_carriers'], 0)
        self.assertEqual(witness['completions'], 1)

    def test_symbol_aliases_and_wrong_carrier_scope_cannot_merge_progress(self):
        for symbols in ({'marker': True}, {'marker': -1}, {'marker': 256}, {'marker': 0, 'other': 0}, {}):
            with self.subTest(symbols=symbols), self.assertRaises(ValueError):
                wire.pack([(marker(), 0)], [(0, ('activate',))], NAMES, symbols)
        e = marker(); e['target'] = 'all_enemies'
        with self.assertRaisesRegex(ValueError, 'sentinel'):
            wire.pack([(e, 0)], [(0, ('activate',))], NAMES, {'marker': 0})

    def test_private_compiler_uses_literal_table_and_separate_nonnumeric_carriers(self):
        from portable_specs import LIMITS as L, FIELDS as F, check_schema
        check_schema()
        spec=importlib.util.spec_from_file_location('counter_driver_test',ROOT/'research/verify-world-target-counters.py')
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        for case in clone_cases():
            words,meta=driver.compile_case(case)
            self.assertEqual(len(words),97464)
            self.assertEqual(words[0],L['TARGET_COUNTER_ABI'])
            self.assertEqual(words[2],len(case['actions']))
            for i,e in enumerate(case['effects']):
                at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']
                self.assertEqual([words[at+F['KIND']],words[at+F['STAT']]],[4,0])
                self.assertEqual(words[L['HEALTH_DEFINITION_BASE']+i*4+3],1)
                self.assertEqual(words[L['TARGET_COUNTER_INPUT_BASE']+wire.POLICY_BASE+i*16+10],meta['states'][e['name']])
            poisoned=copy.deepcopy(case);poisoned['expected']=['CPU state forbidden'];poisoned['native']={'credit':1000000}
            self.assertEqual(words,driver.compile_case(poisoned)[0])


if __name__ == '__main__': unittest.main()
