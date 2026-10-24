"""Real battle/packet reference for the selected common numeric policy."""
import copy
import math
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'research')]
import engine_worker
from calculator import aim, boss_pattern, timeline
from portable_coordinate_physical_common_cases import fixtures
from world_coordinate_physical_common import common_landing, common_policy, observe
from world_coordinate_physical_native import observe as historical


class CommonPhysicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = fixtures()
        cls.answers = {c['name'].split('/')[-1]: observe(c) for c in cls.cases}

    def test_real_battle_and_policy_are_identified_without_mutating_cases(self):
        case = copy.deepcopy(self.cases[0]); before = copy.deepcopy(case)
        result = observe(case)
        self.assertEqual(case, before)
        self.assertEqual(result['reference_kind'], 'deterministic-common-cpu')
        self.assertEqual(result['contract'], 'coordinate-landing-v1')
        self.assertTrue(result['battle'])
        self.assertTrue(all(r['expected'] is True for r in result['physical_pellets']))
        self.assertEqual(sum(len(v['physical_pellets']) for v in self.answers.values()), 27)
        self.assertEqual(sum(len(r['packets']) for v in self.answers.values()
                             for r in v['physical_pellets']), 47)

    def test_threshold_children_do_not_resample_same_shot_damage(self):
        result = self.answers['threshold-snapshot']; rows = result['physical_pellets']
        self.assertEqual([r['packets'][-1]['damage'] for r in rows], [1000]*6+[7000]*6)
        self.assertEqual(result['battle']['team_counts'], [11, 0])
        self.assertEqual(len(rows[0]['packets']), 1)
        # Another integration partition can still leave a positive residue.
        # Preserve its zero-damage packet rather than normalizing it away.
        self.assertGreater(rows[6]['body_fraction'], 0.)
        self.assertEqual([(p['target'], p['damage']) for p in rows[6]['packets']],
                         [('', 0), ('front', 7000)])

    def test_exact_cover_changes_packet_topology_explicitly(self):
        for name, target, damage in [('full-front', 'front', 3000),
                                     ('interrupt-front', 'stop', 2000)]:
            row = self.answers[name]['physical_pellets'][0]
            self.assertEqual(sum(row['landing']['front']), 1.)
            self.assertEqual(row['body_fraction'], 0.)
            self.assertEqual([(p['target'], p['damage']) for p in row['packets']],
                             [(target, damage)])
            # Historical host GL rounding still emits its zero-damage body.
            old = historical(next(c for c in self.cases if c['name'].endswith('/' + name)))
            self.assertEqual(old['physical_pellets'][0]['packets'][0]['damage'], 0)
            self.assertEqual(len(old['physical_pellets'][0]['packets']), 2)

    def test_damage_expansion_and_next_frame_retirement_are_native(self):
        rows = self.answers['two-muzzles-three-pellets']['physical_pellets']
        self.assertEqual(len(rows), 6)
        self.assertTrue(all([p['damage'] for p in r['packets']] == [653, 22]
                            for r in rows))
        rows = self.answers['retirement']['physical_pellets']
        self.assertEqual([r['packets'][-1]['target'] for r in rows],
                         ['front', 'behind', 'behind'])
        self.assertLess(rows[0]['time'], rows[1]['time'])
        for name in ['pierce-reach', 'charge-pierce']:
            for row in self.answers[name]['physical_pellets']:
                self.assertGreater(row['grow'], 0.)
                self.assertEqual([p['target'] for p in row['packets']],
                                 ['', 'front', 'behind'])
                self.assertEqual([p['extra'] for p in row['packets']],
                                 [False, True, True])

    def test_provider_preserves_order_and_original_landing_type(self):
        shapes = [aim.Shape(x=0., y=0., r=100.), aim.Shape(x=0., y=0., r=1.)]
        value = common_landing(0., 0., 10., shapes)
        self.assertIs(type(value), aim.Landing)
        self.assertEqual(value.front, (1., 0.))
        core = common_landing(0., 0., 10., [], aim.Shape(x=0., y=0., r=5.))
        self.assertGreater(core.core_open, 0.)
        self.assertEqual(core.core_open, core.core_under)

    def test_exception_restores_all_process_global_state(self):
        provider, simulate, profiler = boss_pattern.landing, timeline.simulate, sys.getprofile()
        sin, cos, power = math.sin, math.cos, math.pow
        with patch('coordinate_landing_reference.landing', side_effect=ValueError('injected')):
            with self.assertRaises(ValueError):
                observe(self.cases[0])
        self.assertIs(boss_pattern.landing, provider)
        self.assertIs(timeline.simulate, simulate)
        self.assertIs(sys.getprofile(), profiler)
        self.assertEqual((math.sin, math.cos, math.pow), (sin, cos, power))
        self.assertTrue(observe(self.cases[0])['physical_pellets'])

    def test_nonexpected_simulation_rejected_before_native_execution(self):
        with common_policy():
            with self.assertRaisesRegex(ValueError, 'expected mode'):
                timeline.simulate([], config={'rng_mode': 'random'})
        with self.assertRaises(ValueError):
            common_landing(0., 0., 1., [], k=0.)

    def test_shared_cli_records_policy_sources_and_forbids_gpu(self):
        import portable_reference
        spec = importlib.util.spec_from_file_location('physical_common_cli', ROOT/'scripts/nikke_gpu.py')
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'reference.json'
            result = portable_reference.run_reference('coordinate-physical-common', output,
                        write=cli.write, forbid_gpu=cli.forbid_gpu)
            self.assertEqual(result['case_count'], 9)
            self.assertEqual(result['stage'], 'cpu-common-policy-contract')
            self.assertEqual(result['gpu_calls'], dict(build=0, execute=0))
            self.assertEqual(result['packing_calls'], 0)
            report = json.loads(output.read_text())
            self.assertFalse(report['historical_native_equivalence'])
            self.assertFalse(report['calculation_verified'])
            self.assertFalse(report['gpu_supported'])
            for name in ['world_coordinate_physical_common.py',
                         'world_coordinate_physical_common_reference.py',
                         'coordinate_landing_reference.py', 'coordinate_geometry_reference.py']:
                self.assertIn('research/'+name, report['source_sha256'])
            old = output.read_bytes()
            with self.assertRaises(FileExistsError):
                portable_reference.run_reference('coordinate-physical-common', output,
                        write=cli.write, forbid_gpu=cli.forbid_gpu)
            self.assertEqual(output.read_bytes(), old)

    def test_contract_rejects_wrong_packet_topology_amount_and_notification(self):
        from portable_coordinate_physical_common_contracts import verify
        from world_coordinate_physical_common_reference import observe as reference
        case = self.cases[1]; answer, trace = reference(case)
        self.assertTrue(verify(case, answer)['verified'])
        for edit in ['packet', 'damage', 'counter', 'receipt']:
            changed = copy.deepcopy(answer)
            if edit == 'packet': changed['physical_pellets'][0]['packets'].append(
                dict(changed['physical_pellets'][0]['packets'][0], target='', damage=0))
            elif edit == 'damage': changed['physical_pellets'][0]['packets'][0]['damage'] += 1
            elif edit == 'counter': changed['battle']['team_counts'][0] = 0
            else: changed['battle']['actor_pools']['pools'][0][3] = 1
            with self.subTest(edit=edit), self.assertRaises(AssertionError):
                verify(case, changed)


if __name__ == '__main__':
    unittest.main()
