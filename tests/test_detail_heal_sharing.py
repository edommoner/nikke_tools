"""Production recovery sharing, actual carriers and full squad parity."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from verification_session import compare
sp=importlib.util.spec_from_file_location('production_sharing',ROOT/'scripts/verify-heal-sharing.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class HealSharingGPU(unittest.TestCase):
    def verify(self,raw,count):
        cases=[x for x in m.fixtures('new') if x[1].startswith('raw-')==raw];self.assertEqual(len(cases),count)
        for oracle,name,b,x in cases:
            with self.subTest(name=name):self.assertTrue(compare(oracle,name,b,x,'native')['passed'])
    def test_authored_weighted_shares_and_nested_HP_events(self):self.verify(False,20)
    def test_actual_Rem_Nayuta_Crown_and_storage(self):self.verify(True,5)
if __name__=='__main__':unittest.main()
