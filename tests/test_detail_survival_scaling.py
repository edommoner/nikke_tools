"""Full squads through production v36, including raw Moran/Biscuit and owned gear."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_scaling_authored','scripts/verify-survival-scaling.py')
real=load('production_scaling_actual','scripts/verify-survival-scaling-real.py')
class SurvivalScalingGPU(unittest.TestCase):
    def verify(self,verifier,count):
        cases=list(verifier.fixtures());self.assertEqual(len(cases),count);device=v.s.v.v.v.Cuda()
        try:
            for name,b,extra in cases:
                with self.subTest(name=name):
                    compare=verifier.compare if hasattr(verifier,'compare') else verifier.v.compare
                    self.assertTrue(compare(device,name,b,extra,'native')['passed'])
        finally:device.close()
    def test_lost_HP_and_cover_revival(self):self.verify(v,28)
    def test_actual_Moran_Biscuit_squads_and_growth(self):self.verify(real,12)
if __name__=='__main__':unittest.main()
