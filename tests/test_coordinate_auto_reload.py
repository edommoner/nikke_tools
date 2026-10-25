"""Actual native callbacks constrain pending automatic-reload composition."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('auto_reload_test',ROOT/'research/verify-coordinate-auto-reload-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class AutoReloadTests(unittest.TestCase):
    def test_literal_input_does_not_simulate_and_observation_restores(self):
        from calculator import timeline
        cases=a.fixtures();before=copy.deepcopy(cases)
        with patch.object(timeline,'simulate',side_effect=AssertionError('No computed schedule')):
            for c in cases:self.assertEqual(len(a.compile_case(c)[0]),a.INPUT_WORDS)
        self.assertEqual(cases,before)
    def test_canonical_cover_defers_pending_notification_past_next_shot(self):
        from world_coordinate_manual_native import observe
        before=sys.getprofile();c=next(c for c in a.fixtures() if c['name'].endswith('/cover-then-speed-expiry'));n,_=observe(c)
        self.assertIs(sys.getprofile(),before)
        times=[e['time'] for e in n['manual_actions']['events'] if e['owner']==0 and e['kind']=='_auto_reload']
        self.assertTrue(times);self.assertGreater(times[0],.55);self.assertLess(times[0],.65)
        self.assertTrue(all(type(r['pending_auto_reload']) is bool for r in n['manual_actions']['characters']))

    def test_native_latch_survives_an_ineligible_shot_until_later_post_delay(self):
        from world_coordinate_manual_native import observe
        c=next(c for c in a.fixtures() if c['name'].endswith('/pending-at-end-without-listener'));n,_=observe(c)
        self.assertTrue(n['manual_actions']['characters'][0]['pending_auto_reload'])
        self.assertEqual(n['manual_actions']['characters'][0]['ammo'],1)
        self.assertFalse(any(e['kind']=='_auto_reload' for e in n['manual_actions']['events']))

    def test_complete_wire_and_exact_historical_source_projection(self):
        from portable_backend import validate_composed_stride
        from portable_coordinate_auto_reload_source_contract import project_sources
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS)
        golden=json.loads((ROOT/'research/portable-coordinate-mode-actions-short-expected.json').read_text())
        projected=project_sources(ROOT)
        for name,text in projected.items():self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),golden['source_sha256'][name])
        name='gpu/weapon_frame_phases.slang'
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})

if __name__=='__main__':unittest.main()
