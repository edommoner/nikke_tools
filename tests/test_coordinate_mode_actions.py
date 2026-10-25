"""Mode actions retain canonical literal input and actual native witnesses."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('mode_action_test',ROOT/'research/verify-coordinate-mode-actions-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ModeActionTests(unittest.TestCase):
    def test_literal_producer_and_existing_shared_comparison(self):
        from calculator import timeline
        from portable_backend import validate_composed_stride
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        cases=a.fixtures();original=copy.deepcopy(cases)
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle-derived input')):
            for c in cases:
                w,*_=a.compile_case(c);self.assertEqual(len(w),a.INPUT_WORDS)
        self.assertEqual(cases,original);self.assertEqual(len(cases),20)
        self.assertIs(a.compare,a.parent.compare)
        self.assertIs(a.native_reference,a.parent.native_reference)

    def test_native_hold_is_consumed_during_mode(self):
        from world_coordinate_manual_native import observe
        c=next(c for c in a.fixtures() if c['name'].endswith('/hold-active-mode'))
        n,_=observe(c)
        # Actual native controls must consume the authored operation before mode ends.
        self.assertEqual(n['manual_actions']['characters'][0]['sequence_index'],1)
        shots=[r for r in n['sampled_live_shots'] if r['owner']==0 and r['mode']]
        self.assertTrue(shots);self.assertGreaterEqual(shots[0]['time'],.45);self.assertLess(shots[0]['time'],.5)
        self.assertEqual(n['manual_actions']['characters'][0]['phase'],'post_delay')

    def test_conflicting_static_clock_rejected_without_battle(self):
        from calculator import timeline
        c=a.fixtures()[0];c['post_fire_delays'][0]=0
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle in admission')):
            with self.assertRaisesRegex(ValueError,'post-fire delay'):a.compile_case(c)

    def test_exact_historical_source_projection(self):
        from portable_coordinate_mode_actions_source_contract import project_sources
        name='gpu/coordinate_manual_control_runtime.slang'
        expected=json.loads((ROOT/'research/portable-coordinate-burst-control-short-expected.json').read_text())['source_sha256'][name]
        self.assertEqual(hashlib.sha256(project_sources(ROOT)[name].encode()).hexdigest(),expected)
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})

    def test_unregistered_wire_rejected_before_packing_or_native(self):
        spec=importlib.util.spec_from_file_location('mode_action_cli_test',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        import portable_backend
        with patch.object(portable_backend,'validate_composed_stride',side_effect=ValueError('unregistered wire')),patch.object(cli,'prepare_entries') as prepare:
            with self.assertRaisesRegex(ValueError,'unregistered wire'):cli.development_baseline('coordinate-mode-actions',())
            prepare.assert_not_called()

if __name__=='__main__':unittest.main()
