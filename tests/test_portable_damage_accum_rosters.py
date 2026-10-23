"""Complete original definitions and observer invariance for both profiles."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_damage_accum_roster_cases import fixtures
from portable_damage_accum_roster_contracts import verify
from world_damage_accum_roster_native import observe,bare
class DamageAccumRosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.answers=[observe(c)[0] for c in cls.cases]
    def test_original_definitions_and_positive_consumer_paths(self):
        self.assertEqual(len(self.cases),4)
        for c,n in zip(self.cases,self.answers):
            with self.subTest(case=c['name']):verify(c,n)
    def test_tagging_and_observation_leave_battle_and_projectiles_unchanged(self):
        for c,n in zip(self.cases,self.answers):
            clean=copy.deepcopy(n);clean.pop('damage_accumulation')
            with self.subTest(case=c['name']):self.assertEqual(clean,bare(c)[0])
    def test_packing_keeps_every_original_definition_without_mutating_input(self):
        s=importlib.util.spec_from_file_location('damage_roster_test_adapter',ROOT/'research/verify-world-damage-accum-rosters-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        before=copy.deepcopy(self.cases);rows,_=m.prepare()
        self.assertEqual(fixtures(),before)
        for _,_,(c,meta,p,w) in rows:
            self.assertEqual(len(meta['effects']),len(p['effects']));self.assertEqual(len(meta['effects']),73 if c['contract']['profile']=='도로시' else 74)
if __name__=='__main__':unittest.main()
