"""Target core/factor changes are finite, reversible and arithmetic remains pinned."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_aimed_factor_source_contract import ledger,project_sources
from portable_aimed_packet_cases import direct_fixtures
from portable_aimed_packet_contracts import CONTRACTS


class AimedFactorTests(unittest.TestCase):
    def test_exact_source_delta_and_numerical_faults_reject(self):
        project_sources(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            text=(ROOT/name).read_text()
            for change in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace(change['current'],change['baseline'],1)})
        name='gpu/damage_runtime.slang';text=(ROOT/name).read_text()
        for old,new in [('aimedKind==1 || aimedKind==6','aimedKind==1'),('b[S_intercept_dmg_pct],HUNDRED','b[S_part_dmg_pct],HUNDRED'),('f64Mul(coefficient,normal','f64Mul(ONE,normal')]:
            self.assertIn(old,text)
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace(old,new,1)})

    def test_saved_result_comparison_rejects_stale_and_unrelated_sources(self):
        from portable_aimed_factor_retention import validate_sources
        row=ledger(ROOT)['sources']['gpu/damage_runtime.slang']
        before={'gpu/damage_runtime.slang':row['baseline_sha256'],'gpu/unchanged.slang':'a'}
        after={'gpu/damage_runtime.slang':row['current_sha256'],'gpu/unchanged.slang':'a'}
        diag=dict(after,**{'gpu/world_interrupt_aim_diagnostic_entry.slang':'entry'})
        validate_sources(ROOT,before,after,diag)
        for fault in ('baseline','unrelated','diagnostic'):
            a,b,c=copy.deepcopy((before,after,diag))
            if fault=='baseline':a['gpu/damage_runtime.slang']='bad'
            elif fault=='unrelated':b['gpu/unchanged.slang']='bad'
            else:c['gpu/damage_runtime.slang']='bad'
            with self.subTest(fault=fault),self.assertRaises(ValueError):validate_sources(ROOT,a,b,c)

    def test_direct_factor_contracts_do_not_claim_area_packets(self):
        cases=direct_fixtures();self.assertEqual(len(cases),8)
        for case in cases:
            row=CONTRACTS[case['name']]
            self.assertEqual(row['returned_packets'],row['physical_pellets'])
        self.assertEqual(CONTRACTS['aimed-packet-intercept']['interrupt_damage'][:2],[27000,27000])
        self.assertEqual(CONTRACTS['aimed-packet-part-factor-is-distinct']['interrupt_damage'][:2],[18000,18000])
        self.assertEqual(CONTRACTS['aimed-packet-heal-intercept']['hp'][:2],[8600,8600])


if __name__=='__main__':unittest.main()
