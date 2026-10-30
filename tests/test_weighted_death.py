"""Death during frozen allocation must cancel cover without redistributing it."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_reference import digest
from portable_weighted_death_cases import fixtures
from portable_weighted_death_contracts import verify

class WeightedDeath(unittest.TestCase):
    def test_original_cases_and_actual_deaths_remain_bound(self):
        saved=json.loads((ROOT/'tests/fixtures/weighted-death-cpu-v1.json').read_text(encoding='utf-8'))
        self.assertTrue(saved['passed']);self.assertEqual(saved['case_count'],2)
        for case,row in zip(fixtures(),saved['cases']):
            self.assertEqual(row['input_sha256'],digest(case));self.assertEqual(row['native_sha256'],digest(row['native']))
            self.assertEqual(verify(case,row['native']),row['contract'])
    def test_canceled_cover_cannot_be_silently_delivered_or_renormalized(self):
        row=json.loads((ROOT/'tests/fixtures/weighted-death-cpu-v1.json').read_text(encoding='utf-8'))['cases'][0]
        case=fixtures()[0]
        for mutate in (lambda n:n['weighted_incoming']['cover_receipts'][1].update(delivered=True),
                       lambda n:n['weighted_incoming']['snapshots'][-1].update(active_mask=63),
                       lambda n:n['hits'][0].update(down=True)):
            bad=copy.deepcopy(row['native']);mutate(bad)
            with self.assertRaises(AssertionError):verify(case,bad)

if __name__=='__main__':unittest.main()
