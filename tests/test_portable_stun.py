"""Independent native status contracts precede shared GPU execution."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_stun_cases import fixtures,negative_inputs
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L,FIELDS as F,check_schema
from world_projectile_native import observe


class StunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=importlib.util.spec_from_file_location('stun_test_adapter',ROOT/'research/verify-world-stun-short.py')
        cls.adapter=importlib.util.module_from_spec(s);s.loader.exec_module(cls.adapter)
        cls.rows=fixtures();cls.native=[observe(c) for c in cls.rows]

    def test_stun_presence_is_independent_of_authored_magnitude(self):
        for i in (1,2,3):self.assertEqual(self.native[i][0]['shots'][0],0)
        self.assertEqual(self.native[1],self.native[2]);self.assertEqual(self.native[2],self.native[3])
        self.assertEqual(self.native[0][0]['shots'][0],6)

    def test_finite_stun_pauses_weapon_without_inventing_a_new_shot_schedule(self):
        times=lambda i:[s['time'] for s in self.native[i][0]['projectile_shots'] if s['owner']==0]
        self.assertEqual(times(0)[0],0);self.assertEqual(times(4)[0],.3)
        self.assertEqual(len(times(4)),6);self.assertEqual(len(times(7)),3)
        self.assertTrue(all(t<.3 for t in times(7)))
        self.assertGreater(times(28)[0],.5)

    def test_immunity_is_presence_from_any_owner_and_expiry_restores_stun(self):
        self.assertEqual(self.native[5][0]['shots'],self.native[0][0]['shots'])
        self.assertEqual(self.native[6][0]['shots'],self.native[0][0]['shots'])
        self.assertEqual(len(self.native[19][1]),6);self.assertEqual(len(self.native[20][1]),3)
        self.assertEqual(self.native[19][1],self.native[21][1])
        self.assertEqual(len(self.native[16][1]),0);self.assertEqual(len(self.native[17][1]),0)
        self.assertEqual(len(self.native[18][1]),3)

    def test_target_stunned_uses_scoped_enemy_identity_not_a_fixed_body(self):
        self.assertEqual(len(self.native[11][1]),0)
        self.assertEqual(len(self.native[12][1]),3)
        self.assertEqual([len(self.native[i][1]) for i in (22,23,24)],[0,6,6])
        self.assertEqual(len(self.native[30][1]),3)

    def test_unresolved_stun_does_not_consume_a_lazy_selector_as_a_numeric_query(self):
        self.assertEqual(self.native[9][0]['shots'],self.native[0][0]['shots'])
        self.assertEqual(self.native[10][0]['shots'],[0,0,0,0,8])

    def test_stunned_first_burst_candidate_is_reserved_and_recovers_after_expiry(self):
        for i in (27,29):self.assertEqual(self.native[i][0]['manual_control']['burst_users'],[1,4,8])
        self.assertEqual(self.native[25][0]['shots'],self.native[0][0]['shots'])

    def test_pack_preserves_definitions_canonical_immunity_bit_and_schema(self):
        before=copy.deepcopy(self.rows)
        for c in self.rows:self.adapter.suite.compile_case(c)
        self.assertEqual(self.rows,before);check_schema()
        words,_,_=self.adapter.suite.compile_case(self.rows[19])
        self.assertEqual(words[L['DEFINITION_BASE']+F['KIND']],4)
        self.assertEqual(words[L['DEFINITION_EXTRA_BASE']+3],2)
        self.assertEqual(len(negative_inputs(self.adapter.suite.compile_case)),10)

    def test_child_stun_keeps_current_packet_and_reopened_targets_do_not_rebind(self):
        self.assertEqual(self.native[32][0]['shots'][0],1)
        self.assertEqual(len([s for s in self.native[32][0]['projectile_shots'] if s['owner']==0]),1)
        self.assertGreater(len(self.native[33][0]['projectile_shots']),0)
        self.assertGreater(len(self.native[34][0]['boss_log']),1)
        self.assertEqual(len(self.native[35][1]),6)

    def test_private_combat_boundary_still_rejects_unconnected_api_modes(self):
        for effect in (self.rows[2]['effects'][0],self.rows[19]['effects'][0],self.rows[19]['effects'][1]):
            with self.assertRaises(UnsupportedPortable):validate_effect(effect)
            with self.assertRaises(UnsupportedPortable):validate_effect(effect,combat={})
            validate_effect(effect,combat={},world_frame=True)


if __name__=='__main__':unittest.main()
