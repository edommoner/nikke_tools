"""Unmodified original two-enemy skill, real PART exclusion and shared wire."""
import ast,copy,hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from portable_logical_geometry_roster_cases import fixtures
from portable_logical_geometry_roster_contracts import verify
from world_logical_geometry_native import observe
from world_logical_geometry_full_native import prepare_case,observe as observe_full

class LogicalGeometryRosters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.observed={}
        for c in cls.cases[:4]:
            n,_=observe(c);verify(c,n);cls.observed[c['contract']['scenario']]=n

    def test_original_seventy_definitions_and_weapons_are_preserved(self):
        for c in self.cases:
            with patch.object(timeline,'simulate',side_effect=AssertionError('No battle input schedule')):
                before=copy.deepcopy(c);words,domain=prepare_case(c)
            self.assertEqual(c,before);self.assertEqual(len(words),115680)
            self.assertEqual(domain[1]['coordinate_original_input']['prepared_definitions'],70)
            self.assertTrue(domain[1]['coordinate_original_input']['original_weapon_metadata_preserved'])
            self.assertEqual(domain[0]['names'][0],'니힐리스타')

    def test_two_real_enemies_trigger_original_child_and_single_enemy_does_not(self):
        positive=self.observed['two-enemies'];negative=self.observed['one-outside']
        self.assertEqual(len(positive['notices']),1);self.assertEqual(len(positive['child_landings']),2)
        self.assertEqual({r['name'] for r in positive['children']},{'버닝 샷 3'})
        self.assertFalse(negative['notices']);self.assertFalse(negative['children'])

    def test_initial_part_only_packet_does_not_count_as_enemy(self):
        n=self.observed['part-not-enemy']
        self.assertEqual(n['groups'][0]['targets'],[])
        self.assertEqual(n['groups'][1]['targets'],[[0,0,1]])
        self.assertFalse(n['notices']);self.assertFalse(n['child_landings'])
        self.assertTrue(any(r['caster']=='니힐리스타' and r['target']=='real-part' for r in n['battle']['hits']))

    def test_rotated_rectangle_uses_actual_original_two_enemy_consumer(self):
        n=self.observed['rotated-rectangle'];self.assertTrue(n['notices'])
        self.assertEqual(self.cases[3]['logical_geometry'][0]['shape']['rot'],37.)
        bad=copy.deepcopy(n);bad['groups'][1]['targets'][1]=[1,0,1]
        with self.assertRaises(AssertionError):verify(self.cases[3],bad)

    def test_existing_full_observers_share_the_same_original_contract(self):
        _,domain=prepare_case(self.cases[0]);n=observe_full(domain);verify(domain[0],n)
        expected=self.observed['two-enemies']
        self.assertEqual(n['groups'],expected['groups'])
        self.assertEqual(n['group_children'],expected['children'])
        self.assertEqual(n['group_child_landings'],expected['child_landings'])
        self.assertEqual(n['sampled_points'],expected['sampled_points'])
        self.assertEqual(n['sampled_draws'],expected['physical_draws'])

    def test_extracted_comparer_retains_every_pinned_original_check(self):
        fixture=json.loads((ROOT/'tests/fixtures/logical-comparison-extract-v1.json').read_text())
        source=(ROOT/'research/verify-logical-actor-geometry.py').read_text()
        function=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='compare_observed')
        tail=ast.dump(ast.Module(body=function.body[1:],type_ignores=[]),include_attributes=False)
        self.assertEqual(hashlib.sha256(tail.encode()).hexdigest(),fixture['comparison_tail_ast_sha256'])

if __name__=='__main__':unittest.main()
