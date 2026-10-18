import copy,importlib.util,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,run,module_image,UnsupportedDetail,TD,TS,DETAIL_ABI
spec=importlib.util.spec_from_file_location('event_tests',ROOT/'scripts/verify-events-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class EventDescriptorCompilerTests(unittest.TestCase):
 def compile(self,timings):
  e=v.E('test','buff','atk_pct',1);e['trigger']['timing']=timings
  return compile_effects(v.oracle.characters(v.NAMES),[(e,v.NAMES[0])])
 def test_multiple_parameters_and_duplicate_index_entries_are_preserved(self):
  q=self.compile(['received_hit_count:2','received_hit:3','received_hit:3'])['effects'][0]
  self.assertEqual(q[144],3);self.assertEqual([q[TD+i*TS+1] for i in range(3)],[2,3,3]);self.assertTrue(all(q[TD+i*TS]==32 for i in range(3)))
 def test_descriptor_bound_and_multiple_every_entries(self):
  with self.assertRaises(UnsupportedDetail):self.compile([f'on_attack_count:{i}' for i in range(1,10)])
  q=self.compile(['every:0.5s','every:1s','every:1s'])['effects'][0]
  self.assertEqual([q[TD+i*TS+1] for i in range(3)],[.5,1,1])
 def test_bad_descriptor_is_rejected_before_any_gpu_access(self):
  p=self.compile(['on_attack_count:2']);p['effects'][0][TD+1]=.5
  with self.assertRaises(ValueError):run(None,[p],[[0,2,0,0,-1,0,0,0]],[[0,0]],[{n:{'atk':1} for n in v.NAMES}])
 def test_old_abi_is_rejected_even_with_matching_hashes(self):
  original=Path.read_text
  def stale(path,*args,**kwargs):
   text=original(path,*args,**kwargs)
   if path.name in ('detail_effects-sm86.json','detail_effects-build.json'):
    r=json.loads(text);r['abi']='old_abi';return json.dumps(r)
   return text
  with patch.object(Path,'read_text',stale):
   with self.assertRaises(UnsupportedDetail):module_image(SimpleNamespace(compute_capability=(8,6)),'native')
   with self.assertRaises(UnsupportedDetail):module_image(SimpleNamespace(),'ptx')
class EventDescriptorGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from gpu_selector import Cuda,probe
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_independent_cpu_state_and_full_squad_events(self):
  cases=v.verify(self.device,include_real=False)
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
