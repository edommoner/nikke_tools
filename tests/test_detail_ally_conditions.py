"""HP recipient identity and defender composition must agree with pinned CPU."""
import importlib.util, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('ally_conditions_tests',ROOT/'scripts/verify-ally-conditions-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import UnsupportedDetail, compile_effects
from gpu_selector import Cuda, probe

class AllyConditionCompilerTests(unittest.TestCase):
    def test_nonfinite_hp_thresholds_fail_closed(self):
        for threshold in ('nan','inf','-inf'):
            effect=v.E('gate','buff','atk_pct',23,condition=['ally_hp_below:'+threshold])
            with self.assertRaises(UnsupportedDetail):
                compile_effects(v.oracle.characters(v.NAMES),[(effect,v.NAMES[0])])

    def test_defender_owner_is_excluded_and_branches_are_complements(self):
        names=['크라운','리타','앨리스','모더니아','루주']
        effects=[(v.E('yes','buff','atk_pct',23,condition=['has_defender_ally']),names[0]),
                 (v.E('no','buff','atk_pct',23,condition=['no_defender_ally']),names[0])]
        rows=compile_effects(v.oracle.characters(names),effects)['effects']
        self.assertEqual([r[15] for r in rows],[25,25])
        self.assertEqual([r[17] for r in rows],[0,1])

class AllyConditionGPUTests(unittest.TestCase):
    def test_boundaries_healing_and_query_order_match_cpu(self):
        status=probe()
        if not status['available']:self.skipTest(status['reason'])
        device=Cuda()
        try:rows=v.verify(device,'native',quick=True)
        finally:device.close()
        self.assertEqual(len(rows),33)
        self.assertTrue(all(r['passed'] for r in rows),json.dumps([r for r in rows if not r['passed']],ensure_ascii=True))

if __name__=='__main__':unittest.main()
