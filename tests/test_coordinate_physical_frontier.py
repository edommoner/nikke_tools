"""The source frontier and passive oracle must not imply GPU coverage."""
import importlib.util
import sys
import tempfile
import contextlib
import io
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'research')]
from portable_coordinate_frontier import verify


class FrontierTests(unittest.TestCase):
    def test_audit_reuses_public_and_arena_guards_without_battles(self):
        result = verify(ROOT)
        self.assertTrue(result['passed'])
        self.assertTrue(result['private_composed_arena_verified'])
        self.assertIs(type(result['angular_interval_algebra']['sealed_source_matches_current']),bool)
        self.assertFalse(result['angular_interval_algebra']['battle_connected'])
        self.assertFalse(result['public_gpu_admitted'])
        self.assertFalse(result['coordinate_skill_shape_contains_is_physical_landing'])
        self.assertFalse(result['logical_pellets_equal_emitted_packets'])
        numeric=result['deterministic_numeric_primitives']
        self.assertEqual(numeric['reference_kind'],'deterministic-common-cpu')
        self.assertEqual(numeric['contract'],'coordinate-binary64-v1')
        self.assertFalse(numeric['battle_connected'])
        self.assertFalse(numeric['full_numeric_policy_implemented'])
        geometry=result['deterministic_shape_geometry']
        self.assertTrue(geometry['authored_angles_consumed_on_gpu'])
        self.assertFalse(geometry['rotation_matrix_precomputed_on_cpu'])
        self.assertFalse(geometry['radial_integrator_connected'])
        self.assertFalse(geometry['battle_connected'])
        self.assertEqual((result['gpu_calls'], result['native_battle_calls']), (0, 0))
        rows = {r['id']: r for r in result['dependencies']}
        self.assertEqual(len(rows), 7)
        def visit(key, stack):
            self.assertNotIn(key, stack)
            for dep in rows[key]['depends_on']:visit(dep, stack | {key})
        for key in rows:visit(key, set())

    def test_new_interval_source_reports_stale_proof_without_blocking_development(self):
        name='gpu/coordinate_arc_sets.slang';text=(ROOT/name).read_text()
        report=verify(ROOT,{name:text+'\n// source changed, requires a new independent proof\n'})
        self.assertTrue(report['passed'])
        self.assertFalse(report['angular_interval_algebra']['sealed_source_matches_current'])
        self.assertTrue(report['angular_interval_algebra']['requires_new_metal_proof'])
        self.assertFalse(report['calculation_verified'])

    def test_changed_packet_probability_or_observation_requires_review(self):
        base = 'research/upstream/nikke-calc-master/calculator/'
        for name, old, new in [
                (base+'timeline.py', 'L.core_open / wb', 'L.core_under / wb'),
                (base+'timeline.py', 'round(r["damage"] * p)', 'r["damage"] * p'),
                (base+'timeline.py', 'angle=needs_angle(ax, ay, tg, geom.core)', 'angle=False'),
                (base+'aim.py', '_subtract(arcs, covered)', 'arcs'),
                ('research/world_projectile_native.py', 'len({h.damage for h in answer})==1', 'True'),
                ('app/battle_attack_group_runtime.py', 'ev.part_damage or ev.interrupt_damage', 'False')]:
            with self.subTest(name=name, old=old):
                text=(ROOT/name).read_text();self.assertIn(old,text)
                with self.assertRaises(AssertionError):verify(ROOT,{name:text.replace(old,new,1)})

    def test_cli_writes_once_without_backend_or_native_execution(self):
        path=ROOT/'scripts/nikke_gpu.py';spec=importlib.util.spec_from_file_location('frontier_cli',path)
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'report.json'
            with contextlib.redirect_stdout(io.StringIO()),patch.object(cli,'native_hash',side_effect=AssertionError('No native execution')):
                cli.main(['model-check','--out',str(out)])
            self.assertTrue(out.is_file())
            with self.assertRaises(ValueError):cli.main(['model-check','--out',str(out)])


if __name__=='__main__':unittest.main()
