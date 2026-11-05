"""Original Delta definitions are retained; no favorable subset or input amounts."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_heal_charge_roster_cases import fixtures
class HealChargeRostersTests(unittest.TestCase):
    def test_original_two_durations_and_full_definition_count(self):
        s=importlib.util.spec_from_file_location('delta_full_adapter',ROOT/'research/verify-world-heal-charge-rosters-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        rows,_=m.prepare();self.assertEqual(len(rows),4)
        for name,w,(case,metadata,prepared,_) in rows:
            self.assertEqual(len(prepared['effects']),case['contract']['definitions']);self.assertEqual(len(metadata['effects']),case['contract']['definitions'])
            self.assertEqual(case['body']['squad'][0],'델타 : 닌자 시프')
            stats={e['effect'].get('stat') for e in prepared['effects']}
            self.assertTrue({'heal_overcharge_store_atk_pct','accumulate_max_scale_pct','heal_overcharge_discharge'}<=stats)
    def test_factory_has_no_simulation_or_effect_rewriting(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle')):
            cases=fixtures();self.assertEqual([c['contract']['duration'] for c in cases],[3,30,3,30])
if __name__=='__main__':unittest.main()
