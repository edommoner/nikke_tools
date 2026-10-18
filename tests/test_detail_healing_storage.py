"""Production stored-healing lifecycle, quantities and prior124 GPU paths."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from verification_session import compare
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_healing_storage','scripts/verify-healing-storage.py')
extra=load('production_storage_extra','scripts/healing-storage-extra-fixtures.py')
reg=load('production_storage_legacy','scripts/verify-healing-storage-regressions.py')
class HealingStorageGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count)
        for oracle,name,b,x in cases:
            with self.subTest(name=name):self.assertTrue(compare(oracle,name,b,x,'native')['passed'])
    def test_authored_storage_frames(self):self.verify(((v,*x) for x in v.d.fixtures() if not x[0].startswith('raw-')),8)
    def test_overlap_snapshots_HP_predicates_and_revival(self):self.verify(((v,*x) for x in extra.fixtures()),16)
    def test_actual_raw_carriers_favorite_and_parts(self):self.verify(((v,*x) for x in v.d.fixtures() if x[0].startswith('raw-')),5)
    def test_prior124_outgoing_HP_cover_decoy_survival(self):self.verify(reg.fixtures(),124)
if __name__=='__main__':unittest.main()
