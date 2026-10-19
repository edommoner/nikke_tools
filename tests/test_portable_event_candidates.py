"""Immutable candidate layout must retain the original descriptor contract."""
import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import validate_effect
spec=importlib.util.spec_from_file_location('event_candidates_verifier',ROOT/'scripts/verify-portable-combat.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class EventCandidateLayoutTests(unittest.TestCase):
    def case(self,name):return next(c for c in json.loads((ROOT/'tests/fixtures/portable-event-candidates.json').read_text())['cases'] if c['name']==name)
    def test_all_word_boundaries(self):
        words,_=v.compile_case(self.case('event-candidate-word-boundaries'));at=L['EVENT_CANDIDATE_BASE']+32*L['MASK_WORDS']
        self.assertEqual(words[at:at+8],[0x80000000,0x80000001,1,0x80000000,0,0,0,0x80000000])
    def test_duplicate_descriptors_are_not_deduplicated(self):
        words,_=v.compile_case(self.case('received-count-duplicate-descriptors'))
        self.assertEqual(words[L['DEFINITION_BASE']+F['TRIGGER_COUNT']],2)
        self.assertEqual(words[L['EVENT_CANDIDATE_BASE']+32*L['MASK_WORDS']],1)
    def test_received_count_rejects_fractional_or_nonpositive_thresholds(self):
        import copy
        for timing in ('received_hit_count:0','received_hit_count:-1','received_hit_count:1.5'):
            e=copy.deepcopy(self.case('received-count-1')['effects'][0]);e['trigger']['timing']=[timing]
            with self.subTest(timing=timing),self.assertRaises(ValueError):validate_effect(e)
