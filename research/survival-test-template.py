"""Ordinary application modules must preserve whole-squad down/revive ordering."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('production_survival_oracle',ROOT/'scripts/verify-survival-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class SurvivalGPU(unittest.TestCase):
    def test_whole_squad_death_revival_and_health_conditioned_passives(self):
        cases=list(v.fixtures(quick=True))
        cases += [x for x in v.fixtures() if x[0] in ('raw-mode-모더니아-True','raw-hp-passive-앨리스','raw-hp-passive-솔린','raw-new-라푼젤-death')]
        cases += [x for x in v.fixtures() if x[0].startswith('dead-first-b1-') or x[0]=='dead-b2-waits-for-revival']
        cases += [x for x in v.fixtures() if x[0].startswith('dead-b1-ally-')]
        cases += [x for x in v.fixtures() if x[0].startswith('count-limited-class-') or x[0] in ('charge-prefix-does-not-refill','leftmost-living-refills')]
        self.assertEqual(len(cases),25)
        device=v.v.v.v.Cuda()
        try:
            for name,body,extra in cases:
                with self.subTest(name=name):
                    result=v.compare(device,name,body,extra,'native')
                    self.assertTrue(result['passed'],result)
                    if name=='raw-new-라푼젤-death':
                        self.assertTrue(result['cpu_revives'])
        finally:
            device.close()

if __name__=='__main__':unittest.main()
