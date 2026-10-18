"""Worker routing/fallback contracts, independent of battle-formula tests."""
import sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import gpu_service as service
import detail_gpu

class WorkerBatchTests(unittest.TestCase):
 def test_mixed_inputs_compile_only_supported_and_preserve_order(self):
  def engine(body):
   if body.get('_compile_gpu_detail'):
    if body['id']==2:raise detail_gpu.UnsupportedDetail('effect')
    return body['id']
   return {'total_damage':body['id']}
  device=Mock()
  with patch.object(service.engine_worker,'evaluate',side_effect=engine),patch.object(detail_gpu,'evaluate_full_many',return_value=[{'total_damage':1,'compute':{'backend':'cuda_detail'}}]) as evaluate:
   rows,returned=service.evaluate_details([{'id':1},{'id':2},None,{'verify_detail':'invalid'}],device)
  self.assertIs(returned,device);self.assertEqual(evaluate.call_args.args[1],[1])
  self.assertEqual(rows[0]['result']['compute']['backend'],'cuda_detail')
  self.assertEqual(rows[1]['result']['compute']['backend'],'cpu');self.assertIn('unsupported',rows[1]['result']['compute'])
  self.assertTrue(all('error'in r for r in rows[2:]))
 def test_launch_failure_discards_context_and_falls_back_every_member(self):
  device=Mock()
  with patch.object(service.engine_worker,'evaluate',side_effect=lambda b: b if b.get('_compile_gpu_detail') else {'total_damage':b['id']}),patch.object(detail_gpu,'evaluate_full_many',side_effect=RuntimeError('launch')):
   rows,returned=service.evaluate_details([{'id':1},{'id':2}],device)
  self.assertIsNone(returned);device.close.assert_called_once()
  self.assertEqual([r['result']['total_damage'] for r in rows],[1,2]);self.assertTrue(all(r['result']['compute']['backend']=='cpu'for r in rows))
 def test_verification_rejection_uses_existing_cpu_boundary(self):
  gpu={'compute':{'backend':'cuda_detail'}};cpu={'total_damage':7};rejected={'total_damage':7,'compute':{'backend':'cpu','gpu_result_rejected':True}}
  with patch.object(service.engine_worker,'evaluate',side_effect=[{'program':1},cpu]),patch.object(detail_gpu,'evaluate_full_many',return_value=[gpu]),patch.object(service,'resolve_verification',return_value=rejected) as verify:
   rows,_=service.evaluate_details([{'verify_detail':True}],Mock())
  verify.assert_called_once_with(gpu,cpu);self.assertEqual(rows,[{'result':rejected}])
 def test_empty_and_oversized_requests_do_not_launch(self):
  with patch.object(service,'Cuda') as cuda:
   self.assertEqual(service.evaluate_details([]),([],None))
   for bodies in (None,{},[{}]*33):
    with self.assertRaises(ValueError):service.evaluate_details(bodies)
   cuda.assert_not_called()

if __name__=='__main__':unittest.main()
