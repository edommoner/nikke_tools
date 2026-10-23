"""All original Rapi definitions/producer paths without GPU or added queries."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_projectile_chain_roster_cases import fixtures
from world_projectile_chain_native import observe,plain_original
from portable_projectile_chain_contracts import verify
class ProjectileChainRosters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.answers=[observe(c) for c in cls.cases]
    def test_actual_original_profile_has_87_definitions_and_real_handler_callbacks(self):
        for c,(n,t) in zip(self.cases,self.answers):
            with self.subTest(case=c['name']):verify(c,n)
    def test_no_semantic_change_from_observer(self):
        for c,(n,t) in zip(self.cases,self.answers):
            clean=copy.deepcopy(n);clean.pop('projectile_chain')
            with self.subTest(case=c['name']):self.assertEqual((clean,t),plain_original(c))
if __name__=='__main__':unittest.main()
