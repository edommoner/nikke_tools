"""Fresh fixed-source proofs and compiler identities stay scoped to their suites."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','scripts')]


class DeliveryRecertification(unittest.TestCase):
    pass


    def test_historical_goldens_and_certificates_remain_available(self):
        for suite in ('logical-actor-geometry','logical-actor-rosters'):
            for version in (1,2):
                raw=(ROOT/'research'/f'portable-{suite}-v{version}-expected.json').read_bytes()
                c=json.loads((ROOT/'research'/f'portable-compiler-full--{suite}-v{version}-source-certificate.json').read_text())
                self.assertEqual(c['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
    def test_current_recertification_retains_all_prior_battle_results(self):
        for suite in ('logical-actor-geometry','logical-actor-rosters'):
            old=json.loads((ROOT/'research'/f'portable-{suite}-v2-expected.json').read_text())
            new=json.loads((ROOT/'research'/f'portable-{suite}-v3-expected.json').read_text())
            for field in ('entries','input_sha256','output_sha256'):self.assertEqual(old[field],new[field])
            self.assertNotEqual(old['source_sha256'],new['source_sha256'])



if __name__=='__main__':unittest.main()
