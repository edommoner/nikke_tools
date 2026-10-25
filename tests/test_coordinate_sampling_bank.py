import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_coordinate_sampling_bank import LAYOUT,verify,check_schema
from portable_roster_team_history import legacy_view
spec=importlib.util.spec_from_file_location('sampled_battle',ROOT/'research/verify-coordinate-sampled-battle-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class BankTests(unittest.TestCase):
    def test_capacity_and_persistent_rng_do_not_overlap(self):
        check_schema(ROOT);v=verify();self.assertEqual((v['logical_pellets'],v['targets_excluding_body'],v['extra_output_words']),(1024,127,0))
    def test_static_pack_never_runs_a_battle_or_rng(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle packing')):rows,raw=a.prepare()
        self.assertEqual((len(rows),len(raw)),(23,4+23*a.INPUT_WORDS*4));self.assertEqual(len({tuple(w[a.META_BASE+1:a.META_BASE+3]) for _,w,d in rows if d is not None}),8)
    def test_complete_capacity_fits_without_overlapping_persistent_rng(self):
        # Proof is for all 1024 rows, not a reduced practical battle corpus.
        self.assertLessEqual(LAYOUT['ROWS']+1024*12,LAYOUT['META']);self.assertLessEqual(LAYOUT['RNG']+632,919840)
    def test_exact_source_inverse_rejects_unreviewed_sampled_changes(self):
        from portable_coordinate_sampling_source_contract import project_sources,project_backend_source
        project_sources(ROOT);project_backend_source(ROOT)
        name='gpu/coordinate_sampling_runtime.slang'
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n# unreviewed\n')
    def test_exact_overflow_preserves_input_and_all_other_native_fields(self):
        block=[0]*32;block[1]=1024;block[5]=1024;native=dict(team_hits=list(range(2048)),team_counts=[0,1024],damage=[123])
        b,n=legacy_view(block,native,0);self.assertEqual((block[5],len(native['team_hits'])),(1024,2048));self.assertEqual(b[5],0);self.assertEqual(n,dict(native,team_hits=list(range(1024))))
        self.assertEqual([i for i,(x,y) in enumerate(zip(block,b)) if x!=y],[5])
    def test_wrong_omission_retention_and_reserved_bits_never_get_masked(self):
        block=[0]*32;block[1]=1024;block[5]=1024;native=dict(team_hits=list(range(2048)))
        for at in [1,5,6,11]:
            changed=list(block);changed[at]^=1
            with self.assertRaises(AssertionError):legacy_view(changed,native,0)
if __name__=='__main__':unittest.main()
