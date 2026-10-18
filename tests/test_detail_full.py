import copy,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from detail_gpu import evaluate_full,UnsupportedDetail
from gpu_selector import Cuda,probe
from gpu_service import resolve_verification
spec=importlib.util.spec_from_file_location('full_detail_oracle',ROOT/'scripts/verify-full-detail.py');fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
a=fixtures.adapter
class FullDetailedGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_autonomous_five_real_members_180_seconds_and_owned_growth(self):
  report=fixtures.verify(self.device)
  self.assertTrue(report['passed'],json.dumps([c for c in report['cases'] if not c['passed']],ensure_ascii=True))
 def test_equipment_equal_and_distinct_rounding_groups_and_no_cube(self):
  body=fixtures.fixture(12,grown=True)
  for name,entry in body['profile']['chars'].items():
   entry['equip_skills']['max_ammo_pct']=[11.12,11.12,12.34]
   entry['equip_skills']['charge_speed_pct']=[4.3,4.3,6.2]
   entry['cube']={'name':'__none__','level':0}
  body['patches']={}
  gpu=evaluate_full(self.device,a.evaluate({**body,'_compile_gpu_detail':True}));cpu=a.evaluate(body)
  for key in ('total_damage','members','base_stats','burst_timeline'):self.assertEqual(gpu[key],cpu[key],key)
 def test_result_mismatch_is_rejected_and_labelled_cpu(self):
  cpu={'total_damage':100,'members':[{'damage':100}],'base_stats':{},'burst_timeline':[]}
  gpu={**copy.deepcopy(cpu),'total_damage':101,'compute':{'backend':'cuda_detail'}}
  result=resolve_verification(gpu,copy.deepcopy(cpu));self.assertEqual(result['total_damage'],100);self.assertEqual(result['compute']['backend'],'cpu');self.assertTrue(result['compute']['gpu_result_rejected'])
  self.assertFalse(result['compute']['cpu_verification']['matched'])
 def test_policy_mismatch_is_rejected_even_when_damage_is_equal(self):
  cpu={'total_damage':100,'members':[{'damage':100}],'base_stats':{},'burst_timeline':[],
       'burst_policy':'rules','requested_burst_policy':'rules','burst_patterns':{},
       'shooting_policy':'character','burst_gauge_mode':'accumulate','seed':12345}
  for field in ('burst_policy','requested_burst_policy','burst_patterns','shooting_policy','burst_gauge_mode'):
   gpu={**copy.deepcopy(cpu),'compute':{'backend':'cuda_detail'}}
   gpu[field]={'changed':[3]} if field=='burst_patterns' else 'changed'
   result=resolve_verification(gpu,copy.deepcopy(cpu))
   self.assertEqual(result['compute']['backend'],'cpu',field)
   self.assertFalse(result['compute']['cpu_verification'][field+'_equal'],field)
 def test_persistent_worker_routes_gpu_and_unsupported_fallback_and_validation(self):
  body=fixtures.fixture(4,grown=True);body.update(action='evaluate_detail',verify_detail=True)
  process=subprocess.Popen([sys.executable,str(ROOT/'app/gpu_service.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',cwd=ROOT)
  def request(payload,i):
   process.stdin.write(json.dumps({'id':i,'body':payload})+'\n');process.stdin.flush();return json.loads(process.stdout.readline())
  try:
   first=request(body,1)['result'];self.assertEqual(first['compute']['backend'],'cuda_detail');self.assertTrue(first['compute']['cpu_verification']['matched'])
   fallback=copy.deepcopy(body);fallback['squad'][0]='라피 : 레드 후드';fallback['profile']['chars']['라피 : 레드 후드']=fallback['profile']['chars'].pop('모더니아')
   result=request(fallback,2)['result'];self.assertEqual(result['compute']['backend'],'cpu');self.assertTrue(result['compute']['unsupported']);self.assertIn('未対応',result['compute']['fallback_reason'])
   bad={**body,'squad':[body['squad'][0]]*5};self.assertIn('error',request(bad,3))
   again=request(body,4)['result'];self.assertEqual(first['total_damage'],again['total_damage']);self.assertEqual(first['base_stats'],again['base_stats'])
  finally:
   process.stdin.close();process.wait(timeout=30);process.stdout.close();process.stderr.close()
if __name__=='__main__':unittest.main()
