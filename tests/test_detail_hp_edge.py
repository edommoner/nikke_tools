"""Whole-squad HP-edge acceptance through ordinary production modules."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
hp=load('production_hp_authored','scripts/verify-hp-edge.py')
real=load('production_hp_real','scripts/verify-hp-edge-real.py')
ns=load('production_hp_namespace','scripts/verify-hp-edge-namespace.py')
class HPEdgeGPU(unittest.TestCase):
    def verify(self,verifier,count):
        cases=list(verifier.fixtures());self.assertEqual(len(cases),count);device=hp.s.v.v.v.Cuda()
        try:
            for name,b,extra in cases:
                with self.subTest(name=name):self.assertTrue(verifier.compare(device,name,b,extra,'native')['passed'])
        finally:device.close()
    def test_HP_transitions_and_notification_order(self):self.verify(hp,24)
    def test_actual_A2_Soline_and_Flora_whole_squads(self):self.verify(real,12)
    def test_self_HP_and_named_notifications_have_distinct_namespaces(self):self.verify(ns,3)
if __name__=='__main__':unittest.main()
