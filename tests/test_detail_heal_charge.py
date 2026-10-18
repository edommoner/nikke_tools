"""Production received-healing accumulation, discharge and raw Delta squads."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from verification_session import compare
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=load('production_charge','scripts/verify-heal-charge.py');extra=load('production_charge_extra','scripts/verify-heal-charge-extra.py')
class HealChargeGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count)
        for oracle,name,b,x in cases:
            with self.subTest(name=name):self.assertTrue(compare(oracle,name,b,x,'native')['passed'])
    def test_authored_received_healing_capacity_and_release(self):self.verify((x for x in m.fixtures('new') if not x[1].startswith('raw-')),16)
    def test_raw_Delta_Crown_Rem_and_Marciana(self):self.verify((x for x in m.fixtures('new') if x[1].startswith('raw-')),4)
    def test_colliding_lifetimes_capacity_and_nested_release(self):
        # Use the standalone driver's same-frame HP-gain control as well.
        self.verify(((extra,*x) for x in extra.extra.fixtures(extra.m.d)),10)
if __name__=='__main__':unittest.main()
