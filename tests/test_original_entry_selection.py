import engine_worker
"""Selected original diagnostics cannot prepare hidden profiles or certify GPU work."""
import contextlib,copy,hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_original_identity_inventory import selected_profile_bodies,selected_prepared_profiles

class OriginalEntrySelection(unittest.TestCase):
    def test_invalid_selection_fails_before_any_preparation(self):
        invalid=[([],None),(['missing'],None),(['벨벳','missing'],None),(['벨벳','벨벳'],None),([False],None),(['벨벳'],True),(['벨벳'],-1),(['벨벳'],4),(['벨벳'],3),(None,False)]
        with patch.object(engine_worker,'evaluate',side_effect=AssertionError('No preparation')):
            for names,stage in invalid:
                with self.subTest(names=names,stage=stage),self.assertRaises(ValueError):list(selected_prepared_profiles(names,stage))

    def test_all_favorite_snapshots_are_independent_and_original(self):
        with patch.object(engine_worker,'evaluate',side_effect=AssertionError('Metadata only')):rows=selected_profile_bodies(['베이'])
        self.assertEqual([s for _,s,_ in rows],[0,1,2,3])
        self.assertEqual([b['profile']['chars']['베이']['favorite_stage'] for _,_,b in rows],[0,1,2,3])
        before=copy.deepcopy(rows[1]);rows[0][2]['profile']['chars']['베이']['favorite_stage']=99;self.assertEqual(rows[1],before)
        stages=selected_profile_bodies(favorite_stage=3)
        self.assertTrue(stages);self.assertTrue(all(stage==3 for _,stage,_ in stages))

    def test_filter_is_applied_before_evaluate_and_keeps_original_body(self):
        selected=selected_profile_bodies(['벨벳','앤 : 미라클 페어리'],0);expected=[copy.deepcopy(b) for _,_,b in selected];observed=[]
        def prepare(body):observed.append(copy.deepcopy(body));return {'prepared':True}
        with patch.object(engine_worker,'evaluate',side_effect=prepare):rows=list(selected_prepared_profiles(['벨벳','앤 : 미라클 페어리'],0))
        self.assertEqual([(n,s) for n,s,_ in rows],[(n,s) for n,s,_ in selected])
        self.assertEqual(observed,[dict(b,_portable_static_inputs=True) for b in expected])





if __name__=='__main__':unittest.main()
