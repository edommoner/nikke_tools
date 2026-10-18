"""Production whole-squad quantities and prior cover/HP/heal lifecycles."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_capacity','scripts/verify-cover-capacity.py')
reg=load('production_capacity_legacy','scripts/verify-cover-capacity-regressions.py')
cube=load('production_capacity_cubes','scripts/verify-cover-capacity-cube-carriers.py')
class CoverCapacityGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count);device=v.v.s.v.v.v.Cuda()
        try:
            for oracle,name,b,extra in cases:
                with self.subTest(name=name):self.assertTrue(oracle.compare(device,name,b,extra,'native')['passed'])
        finally:device.close()
    def test_authored_cover_capacity(self):self.verify(((v,*x) for x in v.fixtures()),15)
    def test_actual_Tia_cover_cube_owned_growth_and_positions(self):self.verify(((v,*x) for x in v.real_fixtures()),6)
    def test_cover_cube_on_Moran_and_A2(self):self.verify(((cube.cap,*x) for x in cube.fixtures()),2)
    def test_prior_cover_heal_HP_down_lifecycles(self):self.verify(reg.fixtures(),74)
if __name__=='__main__':unittest.main()
