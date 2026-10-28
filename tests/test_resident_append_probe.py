"""Publication regressions and complete state/guard comparisons."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_scope_snapshot_audit import audit_resident_appends
spec=importlib.util.spec_from_file_location('resident_append_test',ROOT/'research/verify-resident-append-short.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


class ResidentAppendTests(unittest.TestCase):
    def pair(self):
        data=json.loads((ROOT/'tests/fixtures/portable-resident-scalar-generated.json').read_text())['appends']
        return data['cuda'].encode(),data['metal'].encode()

    def test_actual_cuda_incremented_index_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'incremented count'):audit_resident_appends(*self.pair())

    def test_actual_metal_scalar_indices_are_an_accepted_publication_shape(self):
        _,metal=self.pair();r=audit_resident_appends(metal,metal)
        self.assertTrue(r['generated_resident_appends_verified']);self.assertFalse(r['calculation_verified'])
        self.assertEqual(len(r['targets']['metal']['appends']),3)

    def test_cache_pair_read_rejects_actual_bad_append_without_actor_scope_marker(self):
        import portable_generation_cache as cache
        cuda,metal=self.pair()
        with tempfile.TemporaryDirectory() as folder:
            paths={k:Path(folder)/k for k in ('cuda','metal')}
            paths['cuda'].write_bytes(cuda);paths['metal'].write_bytes(metal)
            with patch.object(cache,'reflection_plan',return_value={}),patch.object(cache,'verify_cuda_layout_assertions'):
                with self.assertRaisesRegex(ValueError,'incremented count'):cache.validate_pair(paths,'portableEvents')

    def test_nine_cases_cover_last_slots_refresh_owner_dedup_and_all_output_words(self):
        rows,_=probe.prepare();self.assertEqual(len(rows),9)
        self.assertEqual([probe.native_reference(r[2])[2:7] for r in rows],
            [[0,0,0,0,0],[1,0,0,1,1],[512,0,0,512,512],[1,0,0,1,2],
             [0,1,0,1,1],[0,512,0,512,512],[0,1,0,1,2],[0,0,2,0,0],[0,0,2048,0,0]])
        for _,words,domain in rows:
            self.assertEqual(len(words),115680);expected=probe.native_reference(domain);probe.compare(expected,domain)
            for at in (0,2,7,9,32,543,544,1055,1056,1567,1568,3615):
                bad=list(expected);bad[at]^=1
                with self.subTest(case=domain['name'],word=at),self.assertRaises(AssertionError):probe.compare(bad,domain)


if __name__=='__main__':unittest.main()
