"""Whole-squad and named decoy state through ordinary production modules."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from verification_session import compare
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_decoy_heals','scripts/verify-decoy-healing.py')
reg=load('production_decoy_legacy','scripts/verify-decoy-healing-regressions.py')
class DecoyHealingGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count)
        for oracle,name,b,x in cases:
            with self.subTest(name=name):self.assertTrue(compare(oracle,name,b,x,'native')['passed'])
    def test_authored_decoy_frames_and_healing(self):self.verify(((v,*x) for x in v.fixtures()),21)
    def test_actual_Rei_skills_owned_growth_and_down_revival(self):self.verify(((v,*x) for x in v.real_fixtures()),7)
    def test_prior_layers_HP_cover_and_survival(self):self.verify(reg.fixtures(),73)
if __name__=='__main__':unittest.main()
