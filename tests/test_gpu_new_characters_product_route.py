"""Exercise the same public service and CPU-comparison body used by /api/jobs."""
import copy,io,json,struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import engine_worker,portable_detail,portable_detail_service,portable_backend
from engine_gpu_admission import UnsupportedEngineKeys

class DispatchBoundary(BaseException):pass

class NewCharacterProductRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.bodies=json.loads((ROOT/'tests/fixtures/gpu-new-characters-product-v1.json').read_text());[b.update(compute_backend='native_detail') for b in cls.bodies]

    def test_public_service_batch_admits_and_packs_all_three_before_device(self):
        plans=[]
        def device_boundary(prepared):
            plans.extend(prepared)
            self.assertEqual(len(prepared),3)
            for plan in prepared:
                self.assertEqual(plan['source'],'gpu/product_fixed_battle_entry.slang')
                self.assertEqual(plan['backend'],'native')
                self.assertEqual(struct.unpack_from('<I',plan['packed'])[0],1)
                self.assertEqual(len(plan['packed']),4*(1+plan['input_words']))
            raise DispatchBoundary()
        request=dict(action='evaluate_portable_detail_batch',evaluations=copy.deepcopy(self.bodies))
        self.assertTrue(all(body['compute_backend']=='native_detail' and not any(k.startswith('_') for k in body) for body in request['evaluations']))
        with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',NIKKE_DETAIL_CAPTURE_ROOT=folder),patch.object(sys,'stdin',io.StringIO(json.dumps(request))),patch.object(sys,'stdout',io.StringIO()),patch.object(portable_detail,'_execute_prepared',side_effect=device_boundary) as device,patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU fallback before dispatch')) as cpu,patch.object(portable_backend,'execute',side_effect=AssertionError('Real device forbidden')):
            with self.assertRaises(DispatchBoundary):portable_detail_service.main()
            device.assert_called_once();cpu.assert_not_called()
        self.assertEqual(len(plans),3)

    def test_public_single_evaluate_reaches_device_without_cpu_fallback(self):
        for body in self.bodies:
            with self.subTest(character=body['squad'][0]),tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',NIKKE_DETAIL_CAPTURE_ROOT=folder),patch.object(portable_detail,'_execute_prepared',side_effect=DispatchBoundary) as device,patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU fallback before dispatch')) as cpu:
                with self.assertRaises(DispatchBoundary):portable_detail.evaluate(copy.deepcopy(body))
                device.assert_called_once();cpu.assert_not_called()

    def test_ordinary_cpu_comparison_dispatch_admits_shared_backend_body(self):
        # This unflagged body is also used for canonical comparison after GPU
        # readback. Backend routing must retain the shared/legacy distinction.
        with patch.object(portable_backend,'execute',side_effect=AssertionError('No device in CPU comparison')):
            for body in self.bodies:
                with self.subTest(character=body['squad'][0]):
                    result=engine_worker.dispatch(dict(copy.deepcopy(body),action='evaluate'))
                    self.assertGreater(result['total_damage'],0)
                    self.assertEqual(result['engine_revision'],engine_worker.REVISION)


if __name__=='__main__':unittest.main()
