"""Public rounded ratios are candidates, not an invented exact game contract."""
import hashlib,json,sys,unittest
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))

class BayPublishedAllocationTests(unittest.TestCase):
    def test_body_candidate_fits_every_published_survivor_count(self):
        r=json.loads((ROOT/'tests/fixtures/bay-published-allocation-v1.json').read_text())
        with localcontext() as c:
            c.prec=50
            for row in r['without_cover']:
                total=8+3*(row['members']-1)
                for key,weight in [('caster',8),('other',3)]:
                    shown=Decimal(row[key]);actual=Decimal(weight*100)/Decimal(total)
                    self.assertEqual(actual.quantize(Decimal(1).scaleb(shown.as_tuple().exponent),rounding=ROUND_HALF_EVEN),shown)
    def test_cover_disagreement_remains_visible_instead_of_fixing_the_source_table(self):
        r=json.loads((ROOT/'tests/fixtures/bay-published-allocation-v1.json').read_text());row=r['with_cover'][-1]
        with localcontext() as c:
            c.prec=50;candidate=(Decimal(26200)/Decimal(270)).quantize(Decimal('.01'),rounding=ROUND_HALF_EVEN)
        self.assertEqual(candidate,Decimal('97.04'));self.assertEqual(row['cover'],'97.03')
        self.assertTrue(r['inference']['one_member_nearest_rounding_mismatch']);self.assertFalse(r['inference']['exact_cover_weight_verified'])

if __name__=='__main__':unittest.main()
