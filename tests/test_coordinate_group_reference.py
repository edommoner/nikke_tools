"""Coordinate group adapter contracts and transparency, before GPU admission."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from portable_coordinate_group_cases import fixtures
from world_coordinate_group_native import observe
from portable_coordinate_group_contracts import verify
from world_coordinate_physical_common import observe as baseline
from battle_attack_group_runtime import battle_attack_groups,Producer

class CoordinateGroupReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.answers=[observe(c) for c in cls.cases]
    def test_all_authored_contracts_and_inputs(self):
        self.assertEqual(len(self.cases),17)
        for c,(n,t) in zip(self.cases,self.answers,strict=True):self.assertTrue(verify(c,n)['verified'])
        self.assertEqual(self.cases,self.before)
    def test_group_only_identity_scope_preserves_native_battle_packets_and_trace(self):
        for c,(n,trace) in zip(self.cases,self.answers,strict=True):
            if c['name'].split('/')[-1] in ['child-target-body','child-retired-adds','group-buff-next-shot']:continue
            plain=baseline(c);plain_trace=plain.pop('skill_trace')
            self.assertEqual(n['physical_pellets'],plain['physical_pellets'])
            # Group witnesses intentionally activate named buff state. Every
            # other full battle field and the complete skill trace must match.
            self.assertTrue(set(k for k in plain['battle'] if n['battle'][k]!=plain['battle'][k])<= {'named_state'})
            self.assertEqual(trace,plain_trace)
    def test_no_listener_scope_is_fully_transparent(self):
        c=copy.deepcopy(self.cases[0]);pairs=[(e,o) for e,o in zip(c['effects'],c['owners']) if not any(t.startswith('multi_hit:') for t in e['trigger']['timing'])]
        c['effects']=[e for e,o in pairs];c['owners']=[o for e,o in pairs]
        n,trace=observe(c);plain=baseline(c);plain_trace=plain.pop('skill_trace')
        self.assertEqual({k:n[k] for k in plain},plain);self.assertEqual(trace,plain_trace)
        self.assertEqual(n['groups'],[]);self.assertEqual(n['group_receipts'],[])
    def test_literal_contracts_reject_part_as_enemy_or_lost_packet(self):
        c=self.cases[3];native=copy.deepcopy(self.answers[3][0]);native['groups'][0]['targets'].append([1,0,1])
        with self.assertRaises(AssertionError):verify(c,native)
        native=copy.deepcopy(self.answers[3][0]);native['group_shots'][0]['packets']=6
        with self.assertRaises(AssertionError):verify(c,native)
    def test_legacy_scope_still_rejects_coordinate_world_and_default_data_unchanged(self):
        self.assertNotIn('physical_receipts',Producer().data)
        with self.assertRaisesRegex(ValueError,'plain body/add world'):
            with battle_attack_groups(routing='native'):baseline(self.cases[0])
    def test_coordinate_policy_rejects_ambiguous_or_all_enemies_routing(self):
        for kwargs in [dict(routing='all-logical-enemies',coordinate_packets=True),dict(routing='native',coordinate_packets=1)]:
            with self.assertRaises(ValueError):
                with battle_attack_groups(**kwargs):pass
    def test_frontier_distinguishes_reference_adapter_from_gpu_group_connection(self):
        from portable_coordinate_frontier import verify as frontier
        row=next(r for r in frontier(ROOT)['dependencies'] if r['id']=='coordinate-shot-groups')
        self.assertEqual(row['classification'],'gpu_port_gap')
        self.assertTrue(row['native_coordinate_packet_adapter_available'])
        self.assertFalse(row['physical_gpu_group_receipts_connected'])
        self.assertTrue(row['default_plain_packet_policy_preserved'])
    def test_group_scope_restores_native_callbacks_even_after_error(self):
        from calculator import timeline
        before=timeline.CharState._fire
        with self.assertRaisesRegex(RuntimeError,'deliberate'):
            with battle_attack_groups(routing='native',coordinate_packets=True):raise RuntimeError('deliberate')
        self.assertIs(timeline.CharState._fire,before)

if __name__=='__main__':unittest.main()
