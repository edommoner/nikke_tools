"""DoT uses the existing clock and native coordinate phase, not a second timer."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
spec=importlib.util.spec_from_file_location('coordinate_dot_test',ROOT/'research/verify-coordinate-dot-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class CoordinateDotTests(unittest.TestCase):
    def test_all_native_lifetime_and_modifier_contracts(self):
        for c in a.fixtures():
            result=a.native_reference((c,));self.assertEqual(result['battle']['damage'],c['contract']['damage'])
        c=next(c for c in a.fixtures() if c['name'].endswith('dot-layer-ordered-part-product'));self.assertEqual(c['contract']['packets'][:3],[('',6000),('near',7000),('far',7000)])
    def test_static_pack_preserves_input_and_all_coordinate24_inputs(self):
        from calculator import timeline
        c=a.fixtures()[-1];before=copy.deepcopy(c)
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native battle in GPU input')):
            entries,data=a.prepare();old,old_data=a.parent.prepare();a.parent.compile_case(c)
        self.assertEqual(c,before);self.assertEqual(len(entries),35);self.assertEqual(sum(d is not None for _,_,d in entries),28)
        self.assertEqual([w for _,w,_ in entries[:24]],[w for _,w,_ in old]);self.assertEqual(len(data),4+35*a.INPUT_WORDS*4)
    def test_expired_last_tick_uses_geometry_after_its_created_time(self):
        c=next(c for c in a.fixtures() if c['name'].endswith('birth-after-created-final-tick'));n=a.native_reference((c,));t=n['skill_trace'][-1]
        self.assertEqual(t['created'],.2099);self.assertGreater(t['landed'],.21);self.assertEqual(n['coordinate_selection'][-1]['targets'],['near','far'])
if __name__=='__main__':unittest.main()
