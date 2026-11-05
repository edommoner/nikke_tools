"""Live policy observations and literal-only descriptors for shared GPU calls."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
from portable_coordinate_policy_cases import fixtures
from world_coordinate_manual_native import observe
from portable_cover_policy_specs import INPUT_WORDS,INPUT_BASE,MAGIC,empty
s=importlib.util.spec_from_file_location('policy_test',ROOT/'research/verify-coordinate-policy-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.n={c['name'].split('/')[-1]:observe(c)[0] for c in cls.cases}
    def entries(self,label):return [e for e in self.n[label]['manual_actions']['events'] if e['kind']=='_enter_cover']
    def test_native_immutable_and_policy_witnesses(self):
        self.assertEqual(self.cases,self.before);self.assertEqual(len(self.cases),20)
        for label in ('own-full-burst','own-full-burst-extend','before-end','before-end-zero','finish-by-end','own-end-anchor','combat-anchor','named-buff-end','next-cycle','dry-check','gate-open','partial-clips'):
            with self.subTest(label=label):self.assertTrue(self.entries(label))
        for label in ('other-caster-does-not-cover','named-buff-other-owner','named-buff-infinite','gate-closed','cover-disabled'):
            self.assertFalse(self.entries(label))
        self.assertGreaterEqual(sum(e['owner']==0 for e in self.entries('sequence-preempts')),2)
        self.assertTrue(any(k=='cover' for k,v in self.n['sequence-preempts']['cover_policy_state'][0]['reentry']))
    def test_all_inputs_pack_without_running_battles(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native scheduling in packing')):
            for c in self.cases:
                w,m,b,d=a.compile_case(c);self.assertEqual(len(w),109656);self.assertEqual(w[INPUT_BASE],MAGIC)
                self.assertFalse(any(w[INPUT_BASE+8+16:INPUT_BASE+32]))
    def test_empty_extension_is_fixed_and_preserves_old_capacity(self):
        self.assertEqual(len(empty()),128);self.assertEqual(empty()[:8],[MAGIC,1,0,5,24,64,16,0]);self.assertFalse(any(empty()[8:]))
        from portable_backend import validate_composed_stride
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        for source,i,o in [(a.SOURCE,109528,a.OUTPUT_WORDS),(a.parent.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS),(a.SOURCE,a.INPUT_WORDS,1769472)]:
            with self.assertRaises(ValueError):validate_composed_stride(source,i,o)
    def test_history_source_and_transport_inverse_is_strict(self):
        from portable_coordinate_policy_source_contract import project_sources,project_backend_source
        project_sources(ROOT);project_backend_source(ROOT)
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_aim_runtime.slang':(ROOT/'gpu/coordinate_aim_runtime.slang').read_text()+'\n'})
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n')
class PolicyStaticValidationTests(unittest.TestCase):
    def test_cooldown_mismatch_stops_before_battle_or_packing(self):
        c=fixtures()[0];c['combat']['weapons'][0]['cooldown']=.5
        with patch.object(timeline,'simulate',side_effect=AssertionError('No simulation')):
            with self.assertRaisesRegex(ValueError,'cooldown'):a.compile_case(c)

if __name__=='__main__':unittest.main()
