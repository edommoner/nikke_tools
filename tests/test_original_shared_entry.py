"""Stable existing-handler scope, exact legacy inversion and non-certifying inventory."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_coordinate_kind_admission import KindAdmission
class OriginalSharedTests(unittest.TestCase):
    def test_current_wire_and_layout(self):
        from portable_backend import validate_composed_stride
        validate_composed_stride('gpu/world_coordinate_original_shared_entry.slang', 109968, 1769856)
if __name__=='__main__':unittest.main()
