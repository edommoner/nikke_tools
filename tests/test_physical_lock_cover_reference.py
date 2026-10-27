"""Cover must come from actual control producers, with existing battle intact."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_physical_lock_cover_cases import fixtures
# The physical adapter initializes the unchanged native compatibility layers.
ROWS=fixtures()
from world_physical_lock_cover_native import observe
from portable_physical_lock_cover_contracts import verify

class CoverReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results=[observe(c)[0] for c in ROWS]

    def test_actual_owner_other_blocked_empty_and_reload_bound_controls(self):
        for case,native in zip(ROWS,self.results,strict=True):
            with self.subTest(case=case['name']):
                self.assertTrue(verify(case,native)['verified'])
        self.assertEqual([len(n['cover_notifications']) for n in self.results],[1,1,0,1,1])

    def test_no_success_if_cover_clear_is_omitted_or_wrong_caster_clears(self):
        for index in (0,1,2):
            native=copy.deepcopy(self.results[index])
            if index==0:native['clear_events']=[e for e in native['clear_events'] if e['event']!='event:cover']
            else:
                false=copy.deepcopy(self.results[0]['clear_events'][0]);native['clear_events'].insert(0,false)
            with self.subTest(index=index),self.assertRaises(AssertionError):verify(ROWS[index],native)

    def test_no_success_if_attack_snapshot_or_reacquisition_is_changed(self):
        for field in ('handles','revision'):
            native=copy.deepcopy(self.results[0]);native['lock_shots'][0][field]=[] if field=='handles' else 999
            with self.subTest(field=field),self.assertRaises(AssertionError):verify(ROWS[0],native)

    def test_gpu_packer_still_rejects_cover_instead_of_dropping_it(self):
        spec=importlib.util.spec_from_file_location('cover_rejection_physical',ROOT/'research/verify-physical-locks.py')
        suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)
        import portable_backend
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native schedule during packing')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            for case in ROWS:
                with self.subTest(case=case['name']),self.assertRaisesRegex(ValueError,'Non-hold sequence requires common physical control primitives'):
                    suite.compile_case(case)

    def test_reference_registry_and_source_identity_include_dynamic_factory(self):
        from portable_reference import REFERENCES,source_identity
        self.assertEqual(REFERENCES['physical-lock-cover-native'][0],'portable_physical_lock_cover_cases')
        hashes=source_identity()
        for name in ('research/verify-physical-locks.py','research/portable_physical_lock_cover_cases.py','research/world_physical_lock_cover_native.py','research/world_physical_locks_native.py','research/portable_physical_lock_cover_contracts.py'):
            self.assertIn(name,hashes)

if __name__=='__main__':unittest.main()
