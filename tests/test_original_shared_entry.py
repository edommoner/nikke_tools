"""Stable existing-handler scope, exact legacy inversion and non-certifying inventory."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_coordinate_kind_admission import KindAdmission
class OriginalSharedTests(unittest.TestCase):
    def test_source_inverse_and_transport(self):
        from portable_coordinate_original_shared_source_contract import project_sources,project_backend_source
        from portable_coordinate_original_slot_source_contract import project_sources as ancestor
        from portable_backend import validate_composed_stride
        d=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-shared-source-delta.json').read_text());out=project_sources(ROOT)
        for path,r in d['sources'].items():self.assertEqual(out[path],r['baseline'])
        self.assertEqual(project_backend_source(ROOT),d['transport']['baseline']);self.assertNotIn('gpu/world_coordinate_original_shared_entry.slang',ancestor(ROOT));validate_composed_stride('gpu/world_coordinate_original_shared_entry.slang',109968,1769856)
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_vital_kind_admission.slang':(ROOT/'gpu/coordinate_vital_kind_admission.slang').read_text()+'\n'})
if __name__=='__main__':unittest.main()
