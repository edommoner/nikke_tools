"""Control inputs, exact threshold identity, and autonomous GPU/CPU parity."""
import sys,json,copy,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('control_regression',ROOT/'scripts/verify-control-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects,UnsupportedDetail,weapon_rows,TD,TS
from gpu_selector import Cuda,probe
class ControlCompilerTests(unittest.TestCase):
 def test_threshold_spelling_is_identity_and_count_is_independent(self):
  names=v.NAMES;chars=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':v.a.META[n]} for n in names]
  es=[v.E('one','buff','atk_pct',1,event='charge_hold:0.5'),v.E('two','buff','atk_pct',1,event='charge_hold:0.50'),v.E('three','buff','atk_pct',1,event='charge_hold_count:0.5:2')]
  p=compile_effects(chars,[(e,names[2]) for e in es]);ds=[r[TD:TD+TS] for r in p['effects']]
  self.assertEqual([d[0] for d in ds],[39]*3);self.assertEqual([d[4] for d in ds],[.5]*3);self.assertNotEqual(ds[0][3],ds[1][3]);self.assertEqual(ds[0][3],ds[2][3]);self.assertEqual(ds[2][1:3],[2,1])
 def test_public_auto_and_character_policy_prepare_different_controls(self):
  name='길티 : 마이티 바니';body=v.body_for([name]+v.NAMES[:4],5,True)
  auto=v.a.evaluate({**body,'_compile_gpu_detail':True});character=v.a.evaluate({**body,'shooting_policy':'character','_compile_gpu_detail':True})
  self.assertFalse(auto['program']['chars'][0]['_detail_sequences']);self.assertEqual(character['program']['chars'][0]['_detail_sequences'],[[0,2.2]])
  body2=v.body_for(['마스트 : 로망틱 메이드','도라','리타','앨리스','모더니아'],5,True)
  for policy in ['auto','character']:
   prepared=v.a.evaluate({**body2,'shooting_policy':policy,'_compile_gpu_detail':True})['prepared']
   self.assertFalse(prepared.config.get('burst_pattern'))
  with self.assertRaises(ValueError):v.a.evaluate({**body,'shooting_policy':'unknown'})
 def test_unimplemented_controls_and_oversized_schedules_are_rejected(self):
  body=v.body_for(v.NAMES,1)
  for controls in [{v.NAMES[2]:{'cover':{'policy':'own_full_burst'}}},{v.NAMES[2]:{'sequence':[{'t':i,'action':'hold','until':10} for i in range(9)]}}]:
   with v.configured(controls),self.assertRaises(UnsupportedDetail):v.a.evaluate({**body,'_compile_gpu_detail':True})
  compiled=v.a.evaluate({**body,'_compile_gpu_detail':True});compiled['program']['chars'][0]['_detail_controls']=[[0]*12]*9
  with self.assertRaises(ValueError):weapon_rows(compiled['program']['chars'],compiled['base_stats'])
class ControlGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=probe()
  if not p['available']:raise unittest.SkipTest(p['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_ownership_charge_latching_taps_and_camera_query_boundaries(self):
  report=v.verify(self.device,'native',False)
  self.assertTrue(report['passed'],json.dumps([c for c in report['cases'] if not c['passed']],ensure_ascii=True))
 def test_strict_simultaneous_requests_reject_gpu_result(self):
  controls={v.NAMES[i]:{'tap_fire':{'rate':3.6,'release':.03}} for i in [2,4]};body=v.body_for(v.NAMES,1)
  with v.configured(controls,mode='strict'):
   c=v.a.evaluate({**body,'_compile_gpu_detail':True})
   with self.assertRaises((UnsupportedDetail,RuntimeError)):v.evaluate_full(self.device,c)
   with self.assertRaises(ValueError):v.a.evaluate(body)
if __name__=='__main__':unittest.main()
