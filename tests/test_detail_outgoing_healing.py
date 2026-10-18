"""Production CPU-extension/GPU parity for outgoing healing and prior101."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from verification_session import compare
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_outgoing_heals','scripts/verify-outgoing-healing.py')
reg=load('production_outgoing_legacy','scripts/verify-outgoing-healing-regressions.py')
class OutgoingHealingGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count)
        for oracle,name,b,x in cases:
            with self.subTest(name=name):self.assertTrue(compare(oracle,name,b,x,'native')['passed'])
    def test_authored_body_healing_source_and_recipient(self):self.verify(((v,*x) for x in v.fixtures()),19)
    def test_actual_raw_healers_with_owned_healing_cube(self):self.verify(((v,*x) for x in v.real_fixtures()),4)
    def test_prior101_layers_HP_cover_decoy_and_survival(self):self.verify(reg.fixtures(),101)
if __name__=='__main__':unittest.main()
