from detail_gpu import compile_effects
"""Regression checks for weapon modes, including every-frame magazine restoration."""
import sys,json,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('mode_verify','scripts/verify-modes-detail.py');oracle=load('mode_oracle','scripts/verify-detail.py')
class ModeCompilerTests(unittest.TestCase):
 def test_charge_flag_independent_of_weapon_type(self):
  cs=oracle.characters(v.p.NAMES)
  for weapon,charge,expected in [('SG',True,3),('SR',False,1),('MG',None,2)]:
   e=v.mode(weapon,**({'charge':charge} if charge is not None else {}));q=compile_effects(cs,[(e,v.p.NAMES[2])])['effects'][0];self.assertEqual(q[224],expected)
if __name__=='__main__':unittest.main()
