"""Current compiler boundaries; no historical source/token ledger."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_query_boundary_contract import BOUNDARIES,verify

class QueryBoundaryTests(unittest.TestCase):
    def test_current_query_boundaries(self):
        self.assertEqual(len(verify(ROOT)['functions']),6)

    def test_missing_boundary_is_rejected(self):
        for path,names in BOUNDARIES.items():
            source=(ROOT/path).read_text()
            for name in names:
                import re
                changed=re.sub(r'\[noinline\]\n(?=(?:bool|uint|uint64_t) '+name+r'\()', '', source)
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    verify(ROOT,sources={path:changed})
