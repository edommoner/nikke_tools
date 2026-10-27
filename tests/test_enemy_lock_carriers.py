"""Original enemy definitions reach native carriers; no hidden static schedules."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('enemy_lock_suite',ROOT/'research/verify-lock-enemy-carriers.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class EnemyLockTests(unittest.TestCase):
    def test_original_enemy_marker_clear_and_received_damage_definitions_preserved(self):
        original=suite.source_definitions()
        for case in suite.fixtures():
            for i in (0,1,2,6):self.assertIn(original[i],case['effects'])
            before=copy.deepcopy(case);w,meta,b=suite.compile_case(case)
            self.assertEqual(case,before);self.assertEqual(meta['original_lock_marker'],original[0])
            self.assertEqual(len(w),104400)
    def test_packing_does_not_run_native_or_choose_runtime_recipients(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('Static input only')):
            rows,data=suite.prepare()
        self.assertEqual(len(rows),7);self.assertEqual(sum(d is not None for _,_,d in rows),4)
    def test_native_marker_attaches_to_distinct_real_enemies(self):
        c=suite.fixtures()[0];w,m,b=suite.compile_case(c);n=suite.native_reference((c,m,b))
        self.assertEqual([p['receipt'][3:6] for p in n['lock_pulses'][:2]],[[0,0,1],[5,0,1]])
        self.assertEqual([len(s['handles']) for s in n['lock_shots']],[2,2])
        self.assertIn('named_state',n['battle'])
        self.assertTrue(n['battle']['named_state']['context_restored'])
        queries=n['battle']['named_state']['queries']
        self.assertEqual([(q['identity'],q['present'],q['stack']) for q in queries],[(0,True,1),(1,False,0),(0,True,1)])
    def test_exact_source_inverse_and_wire_guard(self):
        from portable_lock_enemy_carrier_source_contract import project_sources
        from portable_backend import validate_composed_stride
        data=json.loads((ROOT/'tests/fixtures/portable-lock-enemy-carrier-source-delta.json').read_text());projected=project_sources(ROOT)
        for name,row in data['sources'].items():
            self.assertEqual(projected[name],row['baseline'])
            with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n// mutation'})
        validate_composed_stride(suite.SOURCE,104400,806912)
        with self.assertRaises(ValueError):validate_composed_stride(suite.SOURCE,104400,786432)
if __name__=='__main__':unittest.main()
