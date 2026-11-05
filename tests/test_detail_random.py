import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('random_tests',ROOT/'scripts/verify-random-target-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects,UnsupportedDetail

class RandomTargetTests(unittest.TestCase):

 def test_shared_seed_validation_and_compiler_target_contract(self):
  body=v.v.v.c.body_for(v.v.v.NAMES,1,True)
  for seed in (None,True,-1,1.5,4294967296,'1'):
   with self.assertRaises(ValueError):v.v.v.c.a.evaluate({**body,'seed':seed,'_compile_detail':True})
  chars=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':v.v.v.c.a.META[n]} for n in v.v.v.NAMES]
  effects=[(v.E('one','buff','atk_pct',10,'allies_random:2'),v.OWNER),(v.E('two','buff','crit_dmg',10,'allies_random:2'),v.OWNER),(v.E('clean','instant','debuff_cleanse',1,'allies_random_with_debuff:2'),v.OWNER)]
  rows=compile_effects(chars,effects)['effects']
  self.assertEqual(rows[0][4],19);self.assertEqual(rows[2][4],20)
  self.assertEqual(rows[0][257],rows[1][257]);self.assertNotEqual(rows[0][257],rows[2][257])
  with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(v.E('too long','instant','ammo_charge_flat',1,['allies_random_with_debuff:5']*5),v.OWNER)])
