"""Independent outer receipts must survive scalar hooks installed later."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_original_catalogue_cases import selected_rows,prepare
from world_coordinate_typed_owner_native import observe
from world_coordinate_sampled_skill_native import creation_indices,trace_view

class NativeCreationScalarScope(unittest.TestCase):
    def test_outer_and_inner_observers_keep_every_real_pending_hit(self):
        # Five seconds reaches the real first burst at4.6s. This regression
        # fixture does not replace the original30s GPU proof inputs.
        row=selected_rows(['original-catalogue/hp-shield/라피 : 레드 후드/favorite-0/30s'])[0]
        row['name']='regression/typed-scalar/pending-burst';row['body']['duration']=5
        row['patterns'][0]['until']['time']=5;row['body']['enemy']['patterns']=copy.deepcopy(row['patterns'])
        row['catalogue_profile']['duration']=5
        case,_=prepare(row);previous=sys.getprofile()
        baseline,_=observe(case)
        with creation_indices(case) as receipts:actual,_=observe(case)
        self.assertIs(sys.getprofile(),previous)
        self.assertEqual(actual,baseline,'Installing an outer observer cannot change any native value')
        self.assertTrue(any(r['row']==17 for r in actual['skill_trace']),'Real burst bonus must be emitted')
        self.assertTrue(any(r['row']==11 for r in actual['skill_trace']),'Real stack explosion must be emitted')
        self.assertEqual(len(receipts),len(actual['skill_trace']))
        normalized=trace_view(actual['skill_trace'],receipts)
        self.assertEqual([r['row'] for r in normalized],[r['row'] for r in actual['skill_trace']])

if __name__=='__main__':unittest.main()
