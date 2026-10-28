"""Hostile literal declarations and preservation of original world owners."""
import copy
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/p) for p in ('app', 'research')]
import engine_worker
from calculator import timeline
from calculator.boss_pattern import validate as patterns
from portable_actor_specs import compile_registry
from portable_enemy_healing_cases import fixtures
from portable_enemy_healing_wire import (LAYOUT, INPUT_WORDS, pack, validate,
                                        compile_enemy_healing, compiler_policy,
                                        check_schema)
from portable_specs import LIMITS as L


class EnemyHealingWire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = []
        with patch.object(timeline, 'simulate', side_effect=AssertionError('No simulated input')):
            for row in fixtures():
                prepared = engine_worker.evaluate(dict(row['body'], _portable_static_inputs=True))
                prepared['enemy'].update(coord=copy.deepcopy(row['coord']), patterns=copy.deepcopy(row['patterns']))
                values = compile_enemy_healing(prepared, row['logical_geometry'], row['enemy_healing'])
                cls.rows.append((row, prepared, values))

    def check(self, wire, prefix, row, bindings):
        from portable_world_schedule_specs import compile_schedule
        graph, parsed = compile_schedule(dict(patterns=row['patterns'], clock='accumulated',
                                             duration=row['body']['duration']), notice_payload=True)
        return validate(wire, prefix, parsed, bindings, graph)

    def test_all_six_original_rosters_and_shader_schema(self):
        check_schema(ROOT)
        self.assertEqual(len(self.rows), 6)
        for row, prepared, (words, meta, bindings, _) in self.rows:
            with self.subTest(case=row['name']):
                self.assertEqual(len(words), INPUT_WORDS)
                self.assertEqual(len(prepared['effects']), 69)
                self.assertEqual(meta['coordinate_original_input']['prepared_definitions'], 69)
                report = self.check(words[LAYOUT['BASE']:], words[:LAYOUT['BASE']], row, bindings)
                self.assertEqual(report['source_nodes'], 4)
                self.assertTrue(report['target_order_preserved'])
                self.assertFalse(any(report[k] for k in ('health_copied', 'clock_copied', 'generations_copied', 'gpu_admitted', 'gpu_wire_connected')))

    def test_prefix_and_original_inputs_are_unchanged(self):
        from portable_logical_geometry_wire import compile_logical_geometry
        for row, prepared, (words, _, _, _) in self.rows:
            before = copy.deepcopy(prepared)
            with compiler_policy(), patch.object(timeline, 'simulate', side_effect=AssertionError('No battle')):
                prefix, _, _, _ = compile_logical_geometry(prepared, row['logical_geometry'])
            self.assertEqual(words[:LAYOUT['BASE']], prefix)
            self.assertEqual(prepared, before)

    def test_target_order_is_not_replaced_by_a_bitset(self):
        row, _, (words, _, bindings, _) = self.rows[0]
        parsed = patterns(row['patterns'], coord=True)
        spec = copy.deepcopy(row['enemy_healing'])
        spec[0]['targets'].reverse()
        other = pack(spec, parsed, bindings)
        original = words[LAYOUT['BASE']:]
        at = LAYOUT['ROW_BASE'] + LAYOUT['TARGET_BASE']
        self.assertEqual(other[at:at+2], original[at:at+2][::-1])
        self.assertNotEqual(other, original)
        self.check(other, words[:LAYOUT['BASE']], row, bindings)

    def test_hostile_raw_headers_counts_amounts_slots_and_padding(self):
        row, _, (words, _, bindings, _) = self.rows[0]
        bank = words[LAYOUT['BASE']:]
        mutations = [(0, 0), (1, 2), (2, 0), (2, 33), (3, 31), (4, 128), (5, 1),
                     (16, 32), (17, 0), (17, 128), (20, 0), (20, 127),
                     (21, bank[20]), (147, 1), (560, 1), (4367, 1)]
        for offset, value in mutations:
            other = list(bank); other[offset] = value
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                self.check(other, words[:LAYOUT['BASE']], row, bindings)
        for amount in (-1., float('nan'), float('inf')):
            other = list(bank); other[18:20] = struct.unpack('<II', struct.pack('<d', amount))
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                self.check(other, words[:LAYOUT['BASE']], row, bindings)
        for value in (True, -1, 2**32):
            other = list(bank); other[19] = value
            with self.assertRaises(ValueError):
                self.check(other, words[:LAYOUT['BASE']], row, bindings)

    def test_detached_source_graph_registry_and_health_cannot_be_trusted(self):
        row, _, (words, _, bindings, _) = self.rows[0]
        for offset in (L['WORLD_FRAME_INPUT_BASE']+16+2,
                       L['WORLD_ACTOR_BINDING_BASE']+8+3,
                       L['WORLD_ACTOR_POOL_DEF_BASE']+12,
                       L['WORLD_ACTOR_POOL_DEF_BASE']+12+2):
            other = list(words[:LAYOUT['BASE']]); other[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.check(words[LAYOUT['BASE']:], other, row, bindings)

    def test_default_compiler_admission_restored_even_after_exception(self):
        from portable_enemy_specs import enemy_buff_plan
        effect = dict(type='buff', stat='heal_received_pct', target='all_enemies')
        self.assertIsNone(enemy_buff_plan(effect))
        with self.assertRaisesRegex(RuntimeError, 'injected'):
            with compiler_policy():
                self.assertIsNotNone(enemy_buff_plan(effect))
                raise RuntimeError('injected')
        self.assertIsNone(enemy_buff_plan(effect))

    def test_nonidle_sources_duplicate_targets_and_hit_health_rejected(self):
        row, _, (_, _, bindings, _) = self.rows[0]
        spec = copy.deepcopy(row['enemy_healing'])
        spec[0]['node'] = 'healing-wave'
        with self.assertRaises(ValueError):
            pack(spec, patterns(row['patterns'], coord=True), bindings)
        spec = copy.deepcopy(row['enemy_healing']); spec[0]['targets'] *= 2
        with self.assertRaises(ValueError):
            pack(spec, patterns(row['patterns'], coord=True), bindings)
        for hp in (dict(hit_hp=100), dict(hp=100., hit_hp=3, hit_hp_after=1.)):
            raw = copy.deepcopy(row['patterns']); raw[0]['spec'] = dict(count=2, **hp)
            parsed = patterns(raw, coord=True); _, bound = compile_registry(parsed, pools=True)
            with self.assertRaises(ValueError):
                pack(row['enemy_healing'], parsed, bound)

    def test_full_source_and_recipient_capacity(self):
        raw = [dict(id='wave', kind='summon', spec=dict(count=127, hp=100.))]
        raw += [dict(id='heal-'+str(i), kind='idle', delay=float(i)) for i in range(31)]
        parsed = patterns(raw, coord=True); _, bound = compile_registry(parsed, pools=True)
        targets = [b.label for b in bound if int(b.kind) == 5]
        spec = [dict(node=p['id'], targets=targets[::-1], amount=1.) for p in raw[1:]]
        bank = pack(spec, parsed, bound)
        self.assertEqual(bank[2:5], [31, 32, 128])
        self.assertEqual(bank[20:147], list(range(127, 0, -1)))
        with self.assertRaises(ValueError):
            pack(spec, parsed + [parsed[-1]], bound)


if __name__ == '__main__':
    unittest.main()
