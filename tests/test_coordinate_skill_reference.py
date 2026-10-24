"""Coordinate observation keeps native selection, accounting and hooks intact."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_skill_cases import fixtures
from world_coordinate_skill_native import observe
from world_parts_skill_native import observe as baseline
from portable_coordinate_skill_contracts import verify
class CoordinateSkillTests(unittest.TestCase):
    def test_all_literal_coordinate_contracts(self):
        rows=fixtures();self.assertEqual(len(rows),25);self.assertEqual(len({c['name'] for c in rows}),25)
        for case in rows:self.assertTrue(verify(case,observe(case)[0])['verified'])
    def test_observer_transparency_input_preservation_and_profile_chain(self):
        case=fixtures()[2];before=copy.deepcopy(case);expected,trace=baseline(case);calls=[];old=sys.getprofile()
        def hook(frame,event,arg):
            if frame.f_code.co_name=='_coord_skill_hits':calls.append(event)
        sys.setprofile(hook)
        try:
            actual,new_trace=observe(case);self.assertIs(sys.getprofile(),hook)
        finally:sys.setprofile(old)
        actual.pop('coordinate_skill');self.assertEqual(actual,expected);self.assertEqual(trace,new_trace);self.assertEqual(case,before);self.assertIn('return',calls)
    def test_wrong_kind_order_and_retired_target_are_rejected(self):
        for index in (2,23-1):
            case=fixtures()[index];native,_=observe(case)
            for mutation in ('kind','order','damage'):
                bad=copy.deepcopy(native)
                if mutation=='kind':bad['coordinate_skill']['selections'][0]['targets'][0]='stop'
                elif mutation=='order':bad['parts_skill_events'][-1],bad['parts_skill_events'][-2]=bad['parts_skill_events'][-2],bad['parts_skill_events'][-1]
                else:bad['damage'][0]+=1
                with self.subTest(index=index,mutation=mutation),self.assertRaises(AssertionError):verify(case,bad)
if __name__=='__main__':unittest.main()
