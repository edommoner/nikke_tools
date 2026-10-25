"""Original revival preserves all definitions, cleanup and live oracle ownership."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_revival_tests',ROOT/'research/verify-coordinate-original-revival-short.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalRevivalTests(unittest.TestCase):
    def test_complete_original_inputs_pack_without_battle(self):
        from calculator import timeline
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle schedule in input')):
            entries,_=adapter.prepare()
        self.assertEqual(len(entries),3)
        for _,words,domain in entries:
            c,m,_,_=domain
            self.assertEqual(len(c['effects']),78)
            self.assertEqual(set(m['binding_source_indices']),set(range(78)))
            self.assertEqual(len(words),adapter.INPUT_WORDS)
            self.assertIs(provider(adapter,domain)[2],adapter.native_reference)

    def test_observer_restores_original_methods_on_exception(self):
        from calculator.buff_manager import BuffManager
        from calculator.timeline import CharState
        from world_revive_native import capture
        methods=[(BuffManager,n) for n in ('knock_down','revive','notify','_resolve_target')]+[(CharState,n) for n in ('on_down','on_revive')]
        before=[getattr(cls,name) for cls,name in methods]
        with self.assertRaisesRegex(RuntimeError,'native failure'):
            with capture(dict(names=adapter.fixtures()[0]['body']['squad'])):raise RuntimeError('native failure')
        self.assertEqual([getattr(cls,name) for cls,name in methods],before)

    def test_real_repeated_down_requires_condition_removal_and_single_revive(self):
        row=adapter.fixtures()[2];c,p=adapter.prepare_case(row);c['expected_downs']=2;before=copy.deepcopy(p)
        _,m,b,d=adapter.compile_coordinate_battle(p);profile=sys.getprofile();native=adapter.native_reference((c,m,b,d))
        self.assertIs(sys.getprofile(),profile);self.assertEqual(p,before)
        self.assertTrue(adapter.verify_witness(c,native))
        forged=copy.deepcopy(native);forged['battle']['allies'][3]['down']=False
        with self.assertRaises(AssertionError):adapter.verify_witness(c,forged)
        forged=copy.deepcopy(native);forged['original_named_removals'][0]['after']=1
        with self.assertRaises(AssertionError):adapter.verify_witness(c,forged)

if __name__=='__main__':unittest.main()
