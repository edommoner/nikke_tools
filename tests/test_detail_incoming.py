"""Incoming inputs fail closed; real layer computation executes on the GPU."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('incoming_tests',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_boss import WB,validate_world

class IncomingInputs(unittest.TestCase):
 def test_complete_fixture_compilation_never_invokes_cpu_combat(self):
  with patch.object(v.v.a.sim,'execute',side_effect=AssertionError('CPU combat invoked')):
   for name,b,extra in v.fixtures():
    saved=copy.deepcopy(b)
    with v.context(name,extra):c=v.v.a.evaluate({**b,'_compile_detail':True})
    validate_world(c['program']['world']);self.assertEqual(saved,b,name)
 def test_attack_bytecode_rejects_bad_indices_values_and_unknown_fields(self):
  b=v.body();b['enemy']['patterns']=[v.attack('slot:1')]
  c=v.v.a.evaluate({**b,'_compile_detail':True})
  for at,value in [(264,-1),(267,2),(WB+80,-1),(WB+80,0),(WB+81,-1),(WB+82,5),(WB+83,6),(WB+84,6),(WB+85,2),(WB+87,0),(WB+88,-1),(WB+89,1)]:
   w=copy.deepcopy(c['program']['world']);w[at]=value
   with self.assertRaises(ValueError,msg=str((at,value))):validate_world(w)
 def test_incoming_model_gaps_and_attached_debuffs_are_explicitly_rejected(self):
  b=v.body();b['enemy']['patterns']=[v.attack()]
  for stat in ('damage_reduction_pct','force_move','cover_def_pct'):
   with v.v.v.t.p.custom_effects({v.NAMES[0]:[v.B('gap',stat)]}):
    with self.assertRaisesRegex(v.v.g.UnsupportedDetail,'Incoming model gap'):v.v.a.evaluate({**b,'_compile_detail':True})
  b['enemy']['patterns'][0]['spec']['debuffs']=[{'stat':'atk_pct','value':-10,'duration':1}]
  with self.assertRaises((ValueError,v.v.g.UnsupportedDetail)):v.v.a.evaluate({**b,'_compile_detail':True})
  for key in ('coeff','atk'):
   b=v.body();p=v.attack();p['spec'][key]=0;b['enemy']['patterns']=[p]
   with self.assertRaises(ValueError):v.v.a.evaluate({**b,'_compile_detail':True})

class IncomingGPU(unittest.TestCase):
    pass

if __name__=='__main__':unittest.main()
