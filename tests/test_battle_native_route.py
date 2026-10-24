"""Real native routing parity and packet-order target destruction."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import engine_worker
from calculator import timeline
from portable_battle_native_route_cases import fixtures
from world_battle_native_route_native import observe
from portable_battle_native_route_contracts import verify
from test_battle_attack_group_runtime import snapshot

class NativeRouteTests(unittest.TestCase):
    def test_literal_inputs_do_not_simulate_or_replace_original_definitions(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native input trace')):
            cases=fixtures();self.assertEqual(len(cases),20)
            for case in cases:
                self.assertEqual(case['routing'],'native')
                prepared=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
                self.assertTrue(prepared['effects'])
    def test_native_route_preserves_entire_original_battle_with_live_adds(self):
        for case in (fixtures()[1],fixtures()[10]):
            before=snapshot();n,_=observe(case);verify(case,n)
            self.assertEqual(snapshot(),before)
            self.assertTrue(n['adds']);self.assertFalse(n['notifications'])
    def test_sg_reselects_after_each_destroyed_add_and_keeps_frozen_children(self):
        for case in [c for c in fixtures() if c['contract'].get('reselection')]:
            before=snapshot();original=copy.deepcopy(case);n,_=observe(case)
            self.assertTrue(verify(case,n)['per_pellet_reselection_verified'])
            self.assertEqual(case,original);self.assertEqual(snapshot(),before)
            changed=copy.deepcopy(n);changed['groups'][0]['targets'].reverse()
            with self.assertRaises(AssertionError):verify(case,changed)
            changed=copy.deepcopy(n);changed['child_landings'][0]['target']=[5,0,2]
            with self.assertRaises(AssertionError):verify(case,changed)
    def test_source_audit_rejects_native_route_rewriting_or_open_policy(self):
        from portable_missing_consumer_audit import verify as audit
        target=(ROOT/'app/battle_attack_group_runtime.py').resolve()
        read=Path.read_text;source=read(target)
        for old,new in [("routing not in ('native','all-logical-enemies')","False"),
                        ("routing=='all-logical-enemies' and current","routing=='native' and current"),
                        ("replace(event,rule='all_enemies')","replace(event,rule='enemies_random')")]:
            self.assertIn(old,source);changed=source.replace(old,new)
            def fake(path,*args,**kwargs):
                return changed if path.resolve()==target else read(path,*args,**kwargs)
            with patch.object(Path,'read_text',fake):
                with self.assertRaises(AssertionError):audit(ROOT)

if __name__=='__main__':unittest.main()
