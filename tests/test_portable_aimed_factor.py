"""Target core/factor changes are finite, reversible and arithmetic remains pinned."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_aimed_packet_cases import direct_fixtures
from portable_aimed_packet_contracts import CONTRACTS


class AimedFactorTests(unittest.TestCase):


    def test_direct_factor_contracts_do_not_claim_area_packets(self):
        cases=direct_fixtures();self.assertEqual(len(cases),8)
        for case in cases:
            row=CONTRACTS[case['name']]
            self.assertEqual(row['returned_packets'],row['physical_pellets'])
        self.assertEqual(CONTRACTS['aimed-packet-intercept']['interrupt_damage'][:2],[27000,27000])
        self.assertEqual(CONTRACTS['aimed-packet-part-factor-is-distinct']['interrupt_damage'][:2],[18000,18000])
        self.assertEqual(CONTRACTS['aimed-packet-heal-intercept']['hp'][:2],[8600,8600])


if __name__=='__main__':unittest.main()
