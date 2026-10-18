"""Regression checks for weapon modes, including every-frame magazine restoration."""
import sys,json,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda,probe
from detail_gpu import run,compile_effects

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('mode_verify','scripts/verify-modes-detail.py');oracle=load('mode_oracle','scripts/verify-detail.py')
class ModeCompilerTests(unittest.TestCase):
 def test_charge_flag_independent_of_weapon_type(self):
  cs=oracle.characters(v.p.NAMES)
  for weapon,charge,expected in [('SG',True,3),('SR',False,1),('MG',None,2)]:
   e=v.mode(weapon,**({'charge':charge} if charge is not None else {}));q=compile_effects(cs,[(e,v.p.NAMES[2])])['effects'][0];self.assertEqual(q[224],expected)
class ModeGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  s=probe()
  if not s['available']:raise unittest.SkipTest(s['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_every_frame_damage_and_ammo_through_entry_and_exit(self):
  for label,effects,seconds in v.scenarios():
   # Ammo instant handlers are installed by simulate(), exercised in the full-squad suite.
   if label=='shot-end-removes-ammo':continue
   with self.subTest(case=label):
    names=v.p.NAMES;cs=oracle.characters(names);es=[(e,n) for n,entries in effects.items() for e in entries];program=oracle.program(cs,es);who=2
    bs={n:{'atk':100000+i*1000,'def':1000,'hp':1000000} for i,n in enumerate(names)}
    script=[[0,0,0,0,0,-1,0,0]]
    for frame in range(8*60):
     t=frame/60
     if frame in (20,240):script.append([t,0,3,who,0,-1,0,0])
     script.extend([[t,3,0,who,0,-1,0,0],[t,2,0,who,-1,frame,0,0]])
    cpu,totals=oracle.oracle(program,script,[31784,17],bs,True);gpu=run(self.device,[program],script,[[31784,17]],[bs])
    for frame,(a,b) in enumerate(zip(cpu,gpu['queries'][0])):
     for k in [35,38,39,40,41,42,44]:self.assertEqual(a[k],b[k],(label,frame,k,a[k],b[k]))
    self.assertEqual(totals,gpu['totals'][0])
 def test_whole_squads_auto_bursts_and_owned_growth(self):
  cases=v.verify(self.device,'native',False)
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
