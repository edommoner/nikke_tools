"""Composition with the real passive observer, not a synthetic shot fixture."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from portable_logical_geometry_cases import fixtures
from world_logical_geometry_full_native import prepare_case,observe
from battle_attack_group_runtime import battle_attack_groups
from coordinate_logical_actor_geometry import logical_actor_geometry

class LogicalGeometryFullNative(unittest.TestCase):
    def test_existing_full_observer_retains_real_shots_packets_rng_and_groups(self):
        before=(timeline.simulate,timeline.CharState._fire,timeline.CharState._charge_fire)
        words,domain=prepare_case(fixtures()[0]);n=observe(domain)
        self.assertEqual(before,(timeline.simulate,timeline.CharState._fire,timeline.CharState._charge_fire))
        self.assertEqual(n['original_input_identity']['definitions'],68)
        self.assertTrue(n['original_input_identity']['chars_config_seed_weapon_verified'])
        self.assertEqual(len(n['physical_pellets']),174)
        self.assertEqual(len(n['sampled_points']),174)
        self.assertEqual(len(n['sampled_draws']),349)
        self.assertEqual(len(n['physical_rng']['state']),624)
        self.assertEqual(len(n['logical_geometry']['shots']),84)
        self.assertEqual(len(n['landed_packets']),184)
        self.assertEqual(len(n['groups']),1)
        self.assertEqual(n['groups'][0]['targets'],[[0,0,1],[5,2,1],[5,1,1],[5,0,1]])
        self.assertEqual(len(n['group_notices']),1)
        self.assertEqual(len(n['group_child_landings']),4)
        self.assertEqual({r['kind'] for r in n['sampled_live_shots']},{'_fire','_charge_fire'})

    def test_wrong_scope_order_rejects_without_alias_leak(self):
        before=timeline.CharState._fire
        with battle_attack_groups(routing='native',coordinate_packets=True):
            grouped=timeline.CharState._fire
            with self.assertRaisesRegex(ValueError,'before passive'):
                with logical_actor_geometry(fixtures()[0]['logical_geometry']):pass
            self.assertIs(timeline.CharState._fire,grouped)
        self.assertIs(timeline.CharState._fire,before)

if __name__=='__main__':unittest.main()
